# Precious Files

This folder contains files that are manually downloaded from their source.

Files are named according to their feature contents (e.g., Addresses, Parcels, Civic Associations) and then
dated by download day. For example:

    Addresses-2025-12-31.geojson
    FDA_contacts-2025-10-12.csv
    Civic_Associations-2024-12-13.geojson

Use this function to load the latest feature file:

        sys.path.append("..")
        from fandu.geo_utils import get_newest_feature_file


Geocoded feature files from RVA GeoHub:  https://richmond-geo-hub-cor.hub.arcgis.com/

* [Addresses](https://richmond-geo-hub-cor.hub.arcgis.com/datasets/674d645c444f4191998f0ebb96e56047_0/explore?location=37.527383%2C-77.493413%2C10.99) - All of the official, mapped inventory of all unit and non-unit-based addresses in the City. Includes only active addresses.

* [Parcels](https://richmond-geo-hub-cor.hub.arcgis.com/datasets/fbfce2aab2a44c05bc0abc2d6ea7e54a_0/explore?location=37.525465%2C-77.493422%2C10.60) - City of Richmond property ownership information, mapped by land ownership (parcels).

* [Civic Associations](https://richmond-geo-hub-cor.hub.arcgis.com/datasets/be39ce592f3e4419babe11d1b967e2f3_0/explore?location=37.528836%2C-77.494197%2C10.96) - Represents civic organization boundaries in the city of Richmond, Virginia.

* [National Historic Districts](https://richmond-geo-hub-cor.hub.arcgis.com/datasets/38bd0df47c6440528c2ef22daaf81883_0/explore?location=37.550339%2C-77.468606%2C14.93) - Represents districts and sites that are listed on the National Register of Historic Places (Federal designation) and the Virginia Landmarks Register (State designation).

* [Neighborhoods](https://richmond-geo-hub-cor.hub.arcgis.com/datasets/7a0ffef23d16461e9728c065f27b2790_0/explore?location=37.525021%2C-77.493427%2C10.73) - City of Richmond Neighborhoods. These are different from civic associations.

* [FDA Contact List](https://fandistrict.org/admin/contacts/) - use the "export" button on this screen to save all contacts to a CSV file.

