GeoJSON / CSV Join and Plot Toolbox

Author: Eliot Morrow
Date created: 12/02/2025

---------------------------

Purpose

This Python toolbox for ArcGIS Pro:
	- Prompts the user to select a CSV file and a GeoJSON file.
	- Converts the GeoJSON to a feature class.
	- Joins attributes from the CSV to the feature class using user-selected join fields.
	- Lets the user choose a display/graph field from the CSV via a dropdown.
	- Adds the joined feature class to the current map with a Graduated Colors symbology.
	- Creates a matplotlib bar chart using the same numeric field used for map display.
	- Prompts the user for where to save the PNG of the graph.

This supports quick visualization of census attribute data (like renter percentages) on a map and in a simple chart.

--------------------------

Data Accessed

The toolbox is designed and tested using:

- ACS renter data CSV (Test_data/renters_story_county.csv)
	- Geography (e.g., “Census Tract 1.01”)
	- Total—Total households—HOUSING TENURE—Renter-occupied housing units—Estimate – renter-occupied households
	- MoE (margin of error %)
- GeoJSON census tract layer (Test_data/renters_story_county.json)
	- GEOIDFQ (full census tract identifier)
	- BASENAME (tract number)
	- NAME (tract label, e.g., “Census Tract 1.01”)
	- Shape_Length
	- Shape_Area
	lat bounds
	lon bounds

---------------------------

How to Run Toolbox

1. Add the toolbox to ArcGIS Pro
	- In ArcGIS Pro, in the Catalog pane, right-click Toolboxes → Add Toolbox, and browse to the .pyt.
2. Open the tool
	- Under the toolbox, double-click “Join GeoJSON to CSV and Plot”.
3. Fill in the parameters
	a. Input CSV File
		- Browse to the CSV file.
	b. Input GeoJSON File
		- Browse to the GeoJSON file.
	c. Output Workspace (GDB or Folder)
		- Choose an existing file geodatabase, or a plain folder (does not matter where).
	d. Output Feature Class Name
		- Type a simple feature class name (e.g., Renters_Tracts).
	e. Join Field in Feature Class (from GeoJSON)
		- A dropdown list of GeoJSON property names will appear.
		- Choose the field that matches the tract identifier in the CSV (NAME).
	f. Join Field in CSV
		- Pick the field in the CSV that matches the GeoJSON join field (Geography).
	g. Display / Graph Field (from CSV)
		- (Total—Total households—HOUSING TENURE—Renter-occupied housing units—Estimate)
	h. Output Graph PNG
		- Choose a folder and filename for the bar chart PNG (does not matter where).

4. Run the tool
