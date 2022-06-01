"use strict";
exports.__esModule = true;
var fs = require("fs");
var path = require("path");
var csv_parse_1 = require("csv-parse");
(function () {
    var csvFilePath = path.resolve(__dirname, 'world-cities_csv.csv');
    var headers = ['name', 'country', 'subCountry', 'geoNameId'];
    var fileContent = fs.readFileSync(csvFilePath, { encoding: 'utf-8' });
    // parse()
    // console.log(parse(fileContent));
    var citiesList;
    (0, csv_parse_1.parse)(fileContent, {
        delimiter: ',',
        columns: headers
    }, function (error, result) {
        if (error) {
            console.error(error);
        }
        console.log(result[1].geoNameId);
    });
})();
