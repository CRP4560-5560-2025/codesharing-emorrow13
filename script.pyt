import arcpy
import os
import json
import matplotlib.pyplot as plt

class Toolbox(object):
    def __init__(self):
        self.label = "GeoJSON / CSV Join and Plot"
        self.alias = "geojsoncsv"
        self.tools = [JoinAndPlot]

class JoinAndPlot(object):
    def __init__(self):
        self.label = "Join GeoJSON to CSV and Plot"
        self.description = "Convert GeoJSON to feature class, join CSV, display layer, and plot a basic graph."
        self.canRunInBackground = False

    def getParameterInfo(self):
        # a. CSV and GeoJSON inputs
        in_csv = arcpy.Parameter(
            displayName="Input CSV File",
            name="in_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        in_csv.filter.list = ["csv"]

        in_geojson = arcpy.Parameter(
            displayName="Input GeoJSON File",
            name="in_geojson",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        in_geojson.filter.list = ["json", "geojson"]

        # b. Output workspace + feature class name
        out_ws = arcpy.Parameter(
            displayName="Output Workspace (GDB or Folder)",
            name="out_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        out_fc_name = arcpy.Parameter(
            displayName="Output Feature Class Name",
            name="out_fc_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        # d. Join field names
        # Feature class join field: GPString, populated as dropdown via updateParameters
        join_fc_field = arcpy.Parameter(
            displayName="Join Field in Feature Class (from GeoJSON)",
            name="join_fc_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        # CSV join field: Field dropdown using parameterDependencies
        join_csv_field = arcpy.Parameter(
            displayName="Join Field in CSV",
            name="join_csv_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        join_csv_field.parameterDependencies = [in_csv.name]

        # e. Display / graph field (from CSV) as drop-down
        display_field = arcpy.Parameter(
            displayName="Display / Graph Field (from CSV)",
            name="display_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        display_field.parameterDependencies = [in_csv.name]

        # g. Output PNG
        out_png = arcpy.Parameter(
            displayName="Output Graph PNG",
            name="out_png",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        out_png.filter.list = ["png"]

        return [
            in_csv,
            in_geojson,
            out_ws,
            out_fc_name,
            join_fc_field,
            join_csv_field,
            display_field,
            out_png,
        ]

    def isLicensed(self):
        return True

    def updateParameters(self, params):
        # Populate GeoJSON join field dropdown from properties keys
        in_geojson = params[1]
        join_fc_field = params[4]

        if in_geojson.altered and in_geojson.value:
            path = in_geojson.valueAsText
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                field_names = set()
                if isinstance(data, dict):
                    feats = data.get("features", [])
                    for feat in feats:
                        props = feat.get("properties", {})
                        if isinstance(props, dict):
                            field_names.update(props.keys())

                join_fc_field.filter.list = sorted(field_names)
            except Exception:
                join_fc_field.filter.list = []

        return

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        in_csv = params[0].valueAsText
        in_geojson = params[1].valueAsText
        out_workspace = params[2].valueAsText
        out_fc_name = params[3].valueAsText
        join_fc_field = params[4].valueAsText
        join_csv_field = params[5].valueAsText
        display_field = params[6].valueAsText
        out_png = params[7].valueAsText

        # Helper: map name/alias -> real field name on a dataset
        def resolve_field(table, text):
            if not text:
                return text
            try:
                for f in arcpy.ListFields(table):
                    if f.name == text or f.aliasName == text:
                        return f.name
            except:
                pass
            return text

        # If saving to a folder, create/use a File GDB inside it
        ws_desc = arcpy.Describe(out_workspace)
        if getattr(ws_desc, "workspaceType", "") == "FileSystem":
            gdb = os.path.join(out_workspace, "ToolOutput.gdb")
            if not arcpy.Exists(gdb):
                arcpy.management.CreateFileGDB(out_workspace, "ToolOutput.gdb")
            internal_ws = gdb
        else:
            internal_ws = out_workspace

        out_fc = os.path.join(internal_ws, out_fc_name)

        if not out_png.lower().endswith(".png"):
            out_png = out_png + ".png"

        # c. Convert GeoJSON to feature class
        arcpy.AddMessage("Converting GeoJSON to feature class...")
        arcpy.conversion.JSONToFeatures(in_geojson, out_fc)

        # Resolve join fields
        fc_join = resolve_field(out_fc, join_fc_field)
        csv_join = resolve_field(in_csv, join_csv_field)

        # Join CSV to feature class
        arcpy.AddMessage("Joining CSV to feature class...")
        arcpy.management.JoinField(
            in_data=out_fc,
            in_field=fc_join,
            join_table=in_csv,
            join_field=csv_join
        )

        # Resolve the joined field name on the feature class
        disp_name_csv = resolve_field(in_csv, display_field)
        disp_name = resolve_field(out_fc, disp_name_csv)

        # Create a numeric copy of that field for symbology/graph (converts strings to floats)
        num_field = (disp_name + "_NUM")[:64]
        existing = [f.name for f in arcpy.ListFields(out_fc)]
        if num_field not in existing:
            arcpy.AddMessage("Creating numeric field '{}' for display/graph...".format(num_field))
            arcpy.management.AddField(
                out_fc,
                num_field,
                "DOUBLE",
                10,
                1,
                field_alias="Percentage of Renters (%)"
            )

            with arcpy.da.UpdateCursor(out_fc, [disp_name, num_field]) as cursor:
                for row in cursor:
                    val = row[0]
                    if val in (None, ""):
                        row[1] = None
                    else:
                        if isinstance(val, str):
                            v = val.replace("±", "").replace("%", "").strip()
                        else:
                            v = val
                        try:
                            row[1] = round(float(v), 1)  # nearest tenth
                        except:
                            row[1] = None
                    cursor.updateRow(row)

        arcpy.AddMessage("Using field '{}' (numeric) for display/graph.".format(num_field))

        # Add to current map and apply Graduated Colors on numeric field
        try:
            arcpy.AddMessage("Adding feature class to current map...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            m = aprx.activeMap
            lyr = m.addDataFromPath(out_fc)

            sym = lyr.symbology
            sym.updateRenderer("GraduatedColorsRenderer")
            sym.renderer.classificationField = num_field
            lyr.symbology = sym
        except Exception as e:
            arcpy.AddWarning("Could not set map symbology: {}".format(e))

        # Create matplotlib graph from joined numeric field
        arcpy.AddMessage("Creating matplotlib graph...")
        x_vals, y_vals = [], []

        with arcpy.da.SearchCursor(out_fc, [fc_join, num_field]) as cursor:
            for key, val in cursor:
                if key is None or val in (None, ""):
                    continue
                try:
                    y = float(val)
                except:
                    continue
                x_vals.append(str(key))
                y_vals.append(y)

        if not x_vals:
            arcpy.AddWarning("No numeric values found for plotting; graph may be empty.")

        plt.figure()
        plt.bar(x_vals, y_vals)
        plt.xticks(rotation=90)
        plt.ylabel("Percentage of Renters (%)")
        plt.title("Renter-Occupied Housing Units")
        plt.tight_layout()
        plt.savefig(out_png, dpi=150)
        plt.close()

        arcpy.AddMessage("Graph saved to: {}".format(out_png))
        arcpy.AddMessage("Feature class saved to: {}".format(out_fc))
