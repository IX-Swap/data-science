"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
exports.__esModule = true;
exports.args = void 0;
/* eslint-disable @typescript-eslint/no-var-requires */
var ethers_1 = require("ethers");
var ts_command_line_args_1 = require("ts-command-line-args");
var Swap = /** @class */ (function () {
    function Swap(id, amount0In, amount1In, amount0Out, amount1Out, oracleAmount0Out, oracleAmount1Out, sender, to, slope, chainId) {
        this.id = id;
        this.amount0In = amount0In;
        this.amount1In = amount1In;
        this.amount0Out = amount0Out;
        this.amount1Out = amount1Out;
        this.sender = sender;
        this.to = to;
        this.slope = slope;
        this.chainId = chainId;
        this.oracleAmount0Out = oracleAmount0Out;
        this.oracleAmount1Out = oracleAmount1Out;
    }
    return Swap;
}());
var Pool = /** @class */ (function () {
    //   poolContract: Contract
    /**
     * Make a pool entity that will perform all verifications and contain important data
     * @param token0 address of the first token
     * @param token1 address of the second token
     * @param pair pair address
     * @param kLast last known K-coefficient value
     * @param isMitigationEnabled true if mitigation is enabled, false if not
     * @param priceToleranceThreshold threshold of acceptable difference between transaction out value and Oracle value
     * @param poolContract contract attached to this pool (to request reserves and some inner info)
     * @param systemFeeRate fee rate of the system attached to the pool
     */
    function Pool(token0, token1, pair, 
    // kLast: BigNumber,
    isMitigationEnabled, priceToleranceThreshold, 
    // poolContract: Contract,
    systemFeeRate, isSecurityPool, chainId) {
        //  constants for performing square root calculation
        this.ONE = ethers_1.BigNumber.from(1);
        this.TWO = ethers_1.BigNumber.from(2);
        //  attach all addresses
        this.token0 = token0;
        this.token1 = token1;
        this.pair = pair;
        //  attach contract, request if pool is security one, get latest known reserves
        // this.poolContract = poolContract
        this.isSecurityPool = isSecurityPool;
        if (!isSecurityPool) {
            this.checkIfSecurity();
        }
        // this.updateReserves()
        //  get latest k-coefficient value, mitigation status, tolerance threshold
        // this.kLast = kLast
        this.isMitigationEnabled = isMitigationEnabled;
        this.priceToleranceThreshold = priceToleranceThreshold;
        this.systemFeeRate = systemFeeRate;
        this.chainId = chainId;
        // ! IMPORTANT: make sure that there will be boolean value at moment, not 'promise' one
        if (this.isSecurityPool) {
            this.checkIfToken0Sec();
            this.checkIfToken1Sec();
        }
    }
    /**
     * verify out values, slippage, liquidity and mitigation check of the swap transaction
     * @param transaction swap transaction verification of which is required
     * @param contract
     * @param isSecurity check if a
     */
    Pool.prototype.verifySwap = function (transaction, isSecurity) {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function () {
            var canConsult, amount0OutWithSystemFee, amount1OutWithSystemFee, reserve0Final, reserve1Final;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0:
                        if (!this.chainId)
                            return [2 /*return*/];
                        return [4 /*yield*/, this.canConsultOracle(transaction)]; //(FACTORY_CONTRACT)
                    case 1:
                        canConsult = _c.sent() //(FACTORY_CONTRACT)
                        ;
                        if (!canConsult) return [3 /*break*/, 3];
                        return [4 /*yield*/, this.consultOracle(transaction)]; //(FACTORY_CONTRACT)
                    case 2:
                        _c.sent(); //(FACTORY_CONTRACT)
                        _c.label = 3;
                    case 3:
                        //  perform initial tranasaction values verification and slippage check
                        this.verifyOutValues(transaction);
                        amount0OutWithSystemFee = this.isToken0Sec
                            ? transaction.amount0Out
                            : transaction.amount0Out.add(transaction.amount0Out.mul(this.systemFeeRate).div(1000));
                        amount1OutWithSystemFee = this.isToken1Sec
                            ? transaction.amount1Out
                            : transaction.amount1Out.add(transaction.amount1Out.mul(this.systemFeeRate).div(1000));
                        //  ensure that reserves are bigger than out values
                        if (!((_a = this.reserve0) === null || _a === void 0 ? void 0 : _a.gt(amount0OutWithSystemFee))) {
                            throw new Error('Reserve has insufficient liquidity');
                        }
                        if (!((_b = this.reserve1) === null || _b === void 0 ? void 0 : _b.gt(amount1OutWithSystemFee))) {
                            throw new Error('Reserve has insufficient liquidity');
                        }
                        reserve0Final = this.reserve0.sub(amount0OutWithSystemFee);
                        reserve1Final = this.reserve1.sub(amount1OutWithSystemFee);
                        /*  perform mitigation check if such property is attached to the current pool and
                        it is possible to consult Oracle at the moment */
                        if (this.isMitigationEnabled && this.isConsultable && reserve0Final && reserve1Final) {
                            return [2 /*return*/, this.verifyMitigation(transaction, reserve0Final, reserve1Final)];
                        }
                        return [2 /*return*/];
                }
            });
        });
    };
    /**
     * update current pool reserves via requesting current reserves values through contract
     */
    Pool.prototype.updateReserves = function (reserve0, reserve1) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                // const record = await this.poolContract.methods.getReserves().call()
                this.reserve0 = reserve0;
                this.reserve1 = reserve1; //bigNumber
                return [2 /*return*/];
            });
        });
    };
    /**
     * ! IMPORTANT: set Oracle responses to the specified variables of amount0Out and amount1Out
     * get Oracle estimated out values (only for those that have not-zero in values)
     * @param contract factory contract to perform request to Oracle
     * @param transaction swap transaction for which it is required to perform check
     */
    Pool.prototype.consultOracle = function (transaction) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                if (transaction.amount0In.gt(0)) {
                    //   const response = await contract.methods.oracleConsult(this.token0, transaction.amount0In, this.token1).call()
                    transaction.oracleAmount1Out = transaction.oracleAmount1Out;
                }
                else {
                    transaction.oracleAmount1Out = transaction.oracleAmount1Out;
                }
                if (transaction.amount1In.gt(0)) {
                    //   const response = await contract.methods.oracleConsult(this.token1, transaction.amount1In, this.token0).call()
                    transaction.oracleAmount0Out = transaction.oracleAmount0Out;
                }
                else {
                    transaction.oracleAmount0Out = transaction.oracleAmount0Out;
                }
                return [2 /*return*/];
            });
        });
    };
    /**
     * request via contract if it is possible to consult Oracle, set response to inner flag
     * @param contract factory contract for performing Oracle request
     */
    Pool.prototype.canConsultOracle = function (tranasaction) {
        return __awaiter(this, void 0, void 0, function () {
            var response;
            return __generator(this, function (_a) {
                response = ((tranasaction.oracleAmount0Out !== undefined) && (tranasaction.oracleAmount1Out !== undefined)) // await contract.methods.oracleCanConsult(this.token0, this.token1).call()
                ;
                this.isConsultable = response;
                return [2 /*return*/, response];
            });
        });
    };
    /**
     * Check if current pool is the security one
     * @param contract pool contract to request if it is security
     */
    Pool.prototype.checkIfSecurity = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                // const response = await this.poolContract.methods.isSecurityPool().call()
                this.isSecurityPool = true;
                return [2 /*return*/];
            });
        });
    };
    /**
     * check if token 0 is a security one
     */
    Pool.prototype.checkIfToken0Sec = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                this.isToken0Sec = true;
                return [2 /*return*/];
            });
        });
    };
    /**
     * check if token 1 is a security one
     */
    Pool.prototype.checkIfToken1Sec = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                this.isToken1Sec = false;
                return [2 /*return*/];
            });
        });
    };
    /**
     * check if out values are valid
     * @param transaction swap-operation values of which is required to verify
     */
    Pool.prototype.verifyOutValues = function (transaction) {
        if (!(transaction.amount0Out.gt(0) || transaction.amount1Out.gt(0))) {
            throw new Error("Transaction has insufficient output amount");
        }
        if (!(this.reserve0 &&
            this.reserve1 &&
            transaction.amount0Out.lt(this.reserve0) &&
            transaction.amount1Out.lt(this.reserve1))) {
            throw new Error("Reserve has insufficient liquidity");
        }
        if (!(transaction.to != this.token0 && transaction.to != this.token1)) {
            throw new Error("Invalid sender address");
        }
    };
    /**
     * check transaction slippage
     * @param transaction swap transaction that requires verification
     */
    Pool.prototype.verifySlippage = function (transaction) {
        //  calculate values with fees
        var amount0InWithFee = transaction.amount0In.mul(this.isSecurityPool ? 990 : 997);
        var amount1InWithFee = transaction.amount1In.mul(this.isSecurityPool ? 990 : 997);
        if (!this.reserve0 || !this.reserve1) {
            throw new Error('Reserves not provided');
        }
        var amount0OutMin = amount1InWithFee
            .mul(this.reserve0.mul(ethers_1.BigNumber.from(1000).sub(ethers_1.utils.parseUnits("".concat(transaction.slope)))))
            .div(this.reserve1.mul(1000).mul(1000).add(amount0InWithFee));
        var amount1OutMin = amount0InWithFee
            .mul(this.reserve1.mul(ethers_1.BigNumber.from(1000).sub(ethers_1.utils.parseUnits("".concat(transaction.slope)))))
            .div(this.reserve0.mul(1000).mul(1000).add(amount1InWithFee));
        if (!(transaction.amount0Out.lt(amount0OutMin) || transaction.amount0Out.eq(amount0OutMin))) {
            throw new Error("Max slippage exceeded");
        }
        if (!(transaction.amount1Out.lt(amount1OutMin) || transaction.amount1Out.eq(amount1OutMin))) {
            throw new Error("Max slippage exceeded");
        }
    };
    /**
     * perform transaction mitigation verification
     * @param transaction swap operation to check
     * @param reserve0Final token 0 final reserve after extracting out value with fee
     * @param reserve1Final token 1 final reserve after extracting out value with fee
     */
    Pool.prototype.verifyMitigation = function (transaction, reserve0Final, reserve1Final) {
        // console.log("Inside verify mitigation")
        // console.log(transaction.amount0In.toString(), transaction.amount0Out.toString())
        // console.log(transaction.amount1In.toString(), transaction.amount1Out.toString())
        // console.log(transaction.oracleAmount0Out.toString(), transaction.oracleAmount1Out.toString())
        // console.log(reserve0Final.toString(), reserve1Final.toString())
        if (!transaction.oracleAmount0Out || !transaction.oracleAmount1Out) {
            throw new Error();
        }
        //  find slice factors
        var sliceFactor0 = this.calculateSliceFactor(reserve0Final, transaction.amount0Out);
        var sliceFactor1 = this.calculateSliceFactor(reserve1Final, transaction.amount1Out);
        //  set difference between out values and oracle estimations, check them to be bigger or equal to 0
        var out0AmountDiff = this.estimateAmountDifference(transaction.oracleAmount0Out, transaction.amount0Out);
        var out1AmountDiff = this.estimateAmountDifference(transaction.oracleAmount1Out, transaction.amount1Out);
        if (!(out0AmountDiff.gte(0) || transaction.amount1In.eq(0))) {
            throw new Error("Out value is smaller or equal to zero");
        }
        if (!(out1AmountDiff.gte(0) || transaction.amount0In.eq(0))) {
            throw new Error("Out value is smaller or equal to zero");
        }
        //  find slice factor curve for each token
        //const testSliceFactor1 = BigNumber.from('101')
        var sliceFactor0Curve = sliceFactor0.mul(this.sqrt(sliceFactor0));
        var sliceFactor1Curve = sliceFactor1.mul(this.sqrt(sliceFactor1));
        sliceFactor0Curve = sliceFactor0Curve.gt(this.priceToleranceThreshold)
            ? this.priceToleranceThreshold
            : sliceFactor0Curve;
        sliceFactor1Curve = sliceFactor1Curve.gt(this.priceToleranceThreshold)
            ? this.priceToleranceThreshold
            : sliceFactor1Curve;
        // console.log(sliceFactor0Curve.toString(), sliceFactor1Curve.toString())
        // console.log(out0AmountDiff.toString(), out1AmountDiff.toString())
        /*  transaction is valid if transaction out value has acceptable difference from Oracle estimation
        or other side incoming value is 0 (therefore, out value will be 0)  */
        if (!(out0AmountDiff.lte(ethers_1.BigNumber.from(100).sub(sliceFactor0Curve)) || transaction.amount1In.eq(0))) {
            // throw new Error(`Mitigation0 ${transaction.id}: OUT_VALUE_TOO_FAR_FROM_ORACLE`)
            throw new Error("Out value too far from Oracle");
        }
        if (!(out1AmountDiff.lte(ethers_1.BigNumber.from(100).sub(sliceFactor1Curve)) || transaction.amount0In.eq(0))) {
            // throw new Error(`Mitigation1 ${transaction.id}: OUT_VALUE_TOO_FAR_FROM_ORACLE`)
            throw new Error("Out value too far from Oracle");
        }
        return true;
    };
    /**
     * find a slice factor for token considering current reserves and transaction out value
     * @param reserve token reserve
     * @param transactionOutAmount transaction out value for respective token
     * @returns slice factor
     */
    Pool.prototype.calculateSliceFactor = function (reserve, transactionOutAmount) {
        if (reserve.gt(transactionOutAmount)) {
            return ethers_1.BigNumber.from(100).sub(ethers_1.BigNumber.from(100).mul(reserve.sub(transactionOutAmount)).div(reserve));
        }
        else {
            return ethers_1.BigNumber.from(100);
        }
    };
    /**
     * find difference between Oracle and transaction out values
     * @param oracleAmountOut Oracle estimated out value
     * @param transactionAmountOut transaction estimated out value
     * @returns amount difference between Oracle and transaction estimations
     */
    Pool.prototype.estimateAmountDifference = function (oracleAmountOut, transactionAmountOut) {
        if (oracleAmountOut.eq(transactionAmountOut)) {
            return ethers_1.BigNumber.from(0);
        }
        else {
            var biggerAmount = this.max(transactionAmountOut, oracleAmountOut);
            var smallerAmount = this.min(transactionAmountOut, oracleAmountOut);
            return ethers_1.BigNumber.from(100).mul(biggerAmount.sub(smallerAmount)).div(biggerAmount.add(smallerAmount).div(2));
        }
    };
    /**
     * get smallest number out of two given
     * @param first first number
     * @param second second number
     * @returns smallest of two numbers
     */
    Pool.prototype.min = function (first, second) {
        return first.lt(second) ? first : second;
    };
    /**
     * get biggest number out of two given
     * @param first first number
     * @param second second number
     * @returns biggest of two numbers
     */
    Pool.prototype.max = function (first, second) {
        return first.gt(second) ? first : second;
    };
    /**
     * calculate square root of given BigNumber
     * @param value value for which square root is required to find
     * @returns square root of given BigNumber
     */
    Pool.prototype.sqrt = function (value) {
        var x = value;
        var z = x.add(this.ONE).div(this.TWO);
        var y = x;
        while (z.sub(y).lt(0)) {
            //  check value not to be negative
            y = z;
            z = x.div(z).add(z).div(this.TWO);
        }
        return y;
    };
    return Pool;
}());
function createPool(options) {
    var pool = new Pool(options.token0, options.token1, options.pair, true, options.priceToleranceThreshold, options.systemFeeRate, true, -1);
    return pool;
}
function getAmountOut(amountIn, reserveIn, reserveOut) {
    var amountInWithFee = amountIn.mul(990);
    var numerator = amountInWithFee.mul(reserveOut);
    var denominator = reserveIn.mul(1000).add(amountInWithFee);
    var amountOut = numerator.div(denominator);
    return amountOut;
}
function verifySwap(balance0, balance1, tokenIn, tokenOut, amountIn, oracleAmountOut) {
    return __awaiter(this, void 0, void 0, function () {
        var reserveIn, reserveOut, amount0In, amount1In, amount0Out, amount1Out, oracleAmount0Out, oracleAmount1Out, transaction, result, e_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    // if tokenIn == 'X'  
                    reserveIn = balance0;
                    reserveOut = balance1;
                    amount0In = amountIn;
                    amount1In = ethers_1.BigNumber.from(0);
                    amount0Out = ethers_1.BigNumber.from(0);
                    amount1Out = getAmountOut(amountIn, reserveIn, reserveOut);
                    oracleAmount0Out = ethers_1.BigNumber.from(0);
                    oracleAmount1Out = oracleAmountOut;
                    if (tokenIn == 'Y') {
                        reserveIn = balance1;
                        reserveOut = balance0;
                        amount0In = ethers_1.BigNumber.from(0);
                        amount1In = amountIn;
                        amount0Out = getAmountOut(amountIn, reserveIn, reserveOut);
                        amount1Out = ethers_1.BigNumber.from(0);
                        oracleAmount0Out = oracleAmountOut;
                        oracleAmount1Out = ethers_1.BigNumber.from(0);
                        ;
                    }
                    transaction = new Swap("id", amount0In, amount1In, amount0Out, amount1Out, oracleAmount0Out, oracleAmount1Out, "sender", "to", 0.05, -1);
                    pool.updateReserves(balance0, balance1);
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, pool.verifySwap(transaction, true)];
                case 2:
                    result = _a.sent();
                    console.log('{ status: "success" }');
                    return [3 /*break*/, 4];
                case 3:
                    e_1 = _a.sent();
                    console.log("{ status: \"failure\", message: \"".concat(e_1.message, "\"}"));
                    return [2 /*return*/];
                case 4: return [2 /*return*/];
            }
        });
    });
}
function check_transaction(balance0, balance1, tokenIn, tokenOut, amountIn, amountOut, oracleOut) {
    return __awaiter(this, void 0, void 0, function () {
        var pool, reserve0, reserve1, amount0In, amount1In, amount0Out, amount1Out, oracleAmount0Out, oracleAmount1Out, transaction, result, e_2;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    pool = createPool({
                        token0: "WBTC",
                        token1: "USDC",
                        pair: 'pair_address',
                        priceToleranceThreshold: ethers_1.BigNumber.from(98),
                        systemFeeRate: ethers_1.BigNumber.from(true ? 4 : 0),
                        id: "swap-".concat(Math.floor(1 + Math.random() * 100000000)),
                        slope: 0.5,
                        isSecurity: true,
                        pairAddress: 'pair',
                        chainId: -1
                    });
                    reserve0 = ethers_1.BigNumber.from(balance0);
                    reserve1 = ethers_1.BigNumber.from(balance1);
                    amount0In = null;
                    amount1In = null;
                    amount0Out = null;
                    amount1Out = null;
                    oracleAmount0Out = null;
                    oracleAmount1Out = null;
                    if (tokenIn == pool.token0) {
                        amount0In = ethers_1.BigNumber.from(amountIn);
                        amount1In = ethers_1.BigNumber.from(0);
                        amount0Out = ethers_1.BigNumber.from(0);
                        amount1Out = ethers_1.BigNumber.from(amountOut);
                        oracleAmount0Out = ethers_1.BigNumber.from(0);
                        oracleAmount1Out = ethers_1.BigNumber.from(oracleOut);
                    }
                    else {
                        amount0In = ethers_1.BigNumber.from(0);
                        amount1In = ethers_1.BigNumber.from(amountIn);
                        amount0Out = ethers_1.BigNumber.from(amountOut);
                        amount1Out = ethers_1.BigNumber.from(0);
                        oracleAmount0Out = ethers_1.BigNumber.from(oracleOut);
                        oracleAmount1Out = ethers_1.BigNumber.from(0);
                    }
                    transaction = new Swap("id", amount0In, amount1In, amount0Out, amount1Out, oracleAmount0Out, oracleAmount1Out, "sender", "to", 0.05, -1);
                    pool.updateReserves(reserve0, reserve1);
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, pool.verifySwap(transaction, true)];
                case 2:
                    result = _a.sent();
                    console.log("success");
                    return [3 /*break*/, 4];
                case 3:
                    e_2 = _a.sent();
                    console.log(e_2);
                    return [2 /*return*/];
                case 4: return [2 /*return*/];
            }
        });
    });
}
function main() {
    return __awaiter(this, void 0, void 0, function () {
        var initialReservesList, diffList, pool, _i, initialReservesList_1, initialReserve, _a, diffList_1, diff, i, reserve0, reserve1, amount1In, amount0Out, oracleAmount0Out, transaction, result, e_3;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    initialReservesList = [5500, 30000, 75000, 150000, 300000, 750000];
                    diffList = [-50, -20, -10, 0, 10, 20];
                    pool = createPool({
                        token0: 'X',
                        token1: 'Y',
                        pair: 'pair_address',
                        priceToleranceThreshold: ethers_1.BigNumber.from(98),
                        systemFeeRate: ethers_1.BigNumber.from(true ? 10 : 3),
                        id: "swap-".concat(Math.floor(1 + Math.random() * 100000000)),
                        slope: 0.5,
                        isSecurity: true,
                        pairAddress: 'pair',
                        chainId: -1
                    });
                    _i = 0, initialReservesList_1 = initialReservesList;
                    _b.label = 1;
                case 1:
                    if (!(_i < initialReservesList_1.length)) return [3 /*break*/, 10];
                    initialReserve = initialReservesList_1[_i];
                    _a = 0, diffList_1 = diffList;
                    _b.label = 2;
                case 2:
                    if (!(_a < diffList_1.length)) return [3 /*break*/, 9];
                    diff = diffList_1[_a];
                    i = 1;
                    _b.label = 3;
                case 3:
                    if (!(i < initialReserve)) return [3 /*break*/, 8];
                    reserve0 = ethers_1.BigNumber.from(initialReserve).mul('1000000000000000000');
                    reserve1 = ethers_1.BigNumber.from(initialReserve).mul('1000000000000000000');
                    amount1In = ethers_1.BigNumber.from(i).mul('1000000000000000000');
                    amount0Out = getAmountOut(amount1In, reserve1, reserve0);
                    oracleAmount0Out = amount0Out.mul(100).div(100 + diff);
                    transaction = new Swap("id", ethers_1.BigNumber.from(0), amount1In, amount0Out, ethers_1.BigNumber.from(0), oracleAmount0Out, ethers_1.BigNumber.from(0), "sender", "to", 0.05, -1);
                    pool.updateReserves(reserve0, reserve1);
                    _b.label = 4;
                case 4:
                    _b.trys.push([4, 6, , 7]);
                    return [4 /*yield*/, pool.verifySwap(transaction, true)
                        // console.log('success')
                    ];
                case 5:
                    result = _b.sent();
                    return [3 /*break*/, 7];
                case 6:
                    e_3 = _b.sent();
                    console.log(i);
                    // console.log(amount0Out.toString())
                    // console.log(oracleAmount0Out.toString())
                    console.log(e_3);
                    return [2 /*return*/];
                case 7:
                    i++;
                    return [3 /*break*/, 3];
                case 8:
                    _a++;
                    return [3 /*break*/, 2];
                case 9:
                    _i++;
                    return [3 /*break*/, 1];
                case 10: return [2 /*return*/];
            }
        });
    });
}
var pool = createPool({
    token0: 'X',
    token1: 'Y',
    pair: 'pair_address',
    priceToleranceThreshold: ethers_1.BigNumber.from(98),
    systemFeeRate: ethers_1.BigNumber.from(true ? 10 : 3),
    id: "swap-".concat(Math.floor(1 + Math.random() * 100000000)),
    slope: 0.5,
    isSecurity: true,
    pairAddress: 'pair',
    chainId: -1
});
exports.args = (0, ts_command_line_args_1.parse)({
    balance_0: { type: String, description: "balance of token 0", optional: true },
    balance_1: { type: String, description: "balance of token 1", optional: true },
    tokenIn: { type: String, description: "address/name of incoming token", optional: true },
    tokenOut: { type: String, description: "address/name of outcoming token", optional: true },
    amountIn: { type: String, description: "amount of incoming token to exchange", optional: true },
    amountOut: { type: String, description: "amount of outgoing token to get for exchange", optional: true },
    oracleOut: { type: String, description: "amount of out token conform Oracle TWAP", optional: true }
});
check_transaction(exports.args.balance_0, exports.args.balance_1, exports.args.tokenIn, exports.args.tokenOut, exports.args.amountIn, exports.args.amountOut, exports.args.oracleOut);
