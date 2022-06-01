import * as fs from "fs";
import * as path from "path";
import { parse } from "csv-parse";

type WorldCity = {
    name: string;
    country: string;
    subCountry: string;
    geoNameId: number;
}

(() => {
    const csvFilePath = path.resolve(__dirname, 'world-cities_csv.csv');
  
    const headers = ['name', 'country', 'subCountry', 'geoNameId'];
  
    const fileContent = fs.readFileSync(csvFilePath, { encoding: 'utf-8' });

    // parse()
  
    // console.log(parse(fileContent));

    let citiesList: Array<WorldCity>

    parse(fileContent, {
        delimiter: ',',
        columns: headers,
      }, (error, result: WorldCity[]) => {
        if (error) {
          console.error(error);
        }
    
        console.log(result[1].geoNameId)
      });
  })();



type Swap = {
    id: string,
    token_in: string,
    token_out: string,
    token_in_amount: string,
    token_out_amount: string,
    system_fee: string,
    mitigator_check_status: string,
    oracle_amount_out: string,
    out_amount_diff: string,
    slice_factor: string,
    slice_factor_curve: string,
    status: string,
    block_number: string,
    block_timestamp: string,
    transaction_timestamp: string,
    txd: string,
    sender: string,
    to: string,
    transaction_id: string,
    reserve_X_before: string,
    reserve_Y_before: string,
    k_before: string,
    price_X_cumulative_before: string,
    price_Y_cumulative_before: string,
    is_volatility_mitigator_on_before: string,
    reserve_X: string,
    reserve_Y: string,
    k: string,
    price_X_cumulative: string,
    price_Y_cumulative: string,
    is_volatility_mitigator_on: string,
    X_price: string,
    price_diff: string,
    js_mitigation_status: string
}


(() => {
    const csvFilePath = path.resolve(__dirname, 'world-cities_csv.csv');
  
    const headers = ["id", "token_in", "token_out", "token_in_amount", "token_out_amount_min", 
                    "token_out_amount", "system_fee", "mitigator_check_status", "oracle_amount_out",	
                    "out_amount_diff", "slice_factor", "slice_factor_curve", "status",
                    "block_number", "block_timestamp", "transaction_timestamp", "txd", "sender",
                    "to", "transaction_id",	"reserve_X_before", "reserve_Y_before", "k_before", "price_X_cumulative_before",
                    "price_Y_cumulative_before", "is_volatility_mitigator_on_before", "reserve_X", "reserve_Y",	
                    "k", "price_X_cumulative", "price_Y_cumulative", "is_volatility_mitigator_on", "X_price",	
                    "price_diff", "js_mitigation_status"];
  
    const fileContent = fs.readFileSync(csvFilePath, { encoding: 'utf-8' });

    // parse()
  
    // console.log(parse(fileContent));

    let citiesList: Array<WorldCity>

    parse(fileContent, {
        delimiter: ',',
        columns: headers,
      }, (error, result: WorldCity[]) => {
        if (error) {
          console.error(error);
        }
    
        console.log(result[1].geoNameId)
      });
  })();