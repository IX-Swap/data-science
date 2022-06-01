/* eslint-disable @typescript-eslint/no-var-requires */
import { BigNumber, utils } from 'ethers'
import { parse } from 'ts-command-line-args';

class Swap {
  /*
  For verification required token0 and token1 addresses, amount in for both tokens, amount out for both tokens, to address, slope
  */
  id: string
  amount0In: BigNumber
  amount1In: BigNumber
  amount0Out: BigNumber
  amount1Out: BigNumber
  oracleAmount0Out: BigNumber | undefined
  oracleAmount1Out: BigNumber | undefined
  sender: string
  to: string
  slope: number
  chainId: number

  constructor(
    id: string,
    amount0In: BigNumber,
    amount1In: BigNumber,
    amount0Out: BigNumber,
    amount1Out: BigNumber,
    oracleAmount0Out: BigNumber|undefined,
    oracleAmount1Out: BigNumber|undefined,
    sender: string,
    to: string,
    slope: number,
    chainId: number
  ) {
    this.id = id
    this.amount0In = amount0In
    this.amount1In = amount1In
    this.amount0Out = amount0Out
    this.amount1Out = amount1Out
    this.sender = sender
    this.to = to
    this.slope = slope
    this.chainId = chainId
    this.oracleAmount0Out = oracleAmount0Out
    this.oracleAmount1Out = oracleAmount1Out
  }
}

class Pool {
  //  tokens addresses and pair address
  token0: string
  token1: string
  pair: string

  //  reserves
  reserve0?: BigNumber
  reserve1?: BigNumber

  //  fee rate and isSecurity flag
  systemFeeRate: BigNumber

  //  flags to check if pool is security and if token0 or token1 are the security ones
  isSecurityPool?: boolean
  isToken0Sec?: boolean
  isToken1Sec?: boolean
  chainId: number

  //  flag if pool can be consulted with Oracle
  isConsultable?: boolean

  //  flag defining if mitigation is enabled
  isMitigationEnabled: boolean

  //  constants for performing square root calculation
  ONE: BigNumber = BigNumber.from(1)
  TWO: BigNumber = BigNumber.from(2)

  //  threshold of acceptable difference between transaction out value and Oracle out value
  priceToleranceThreshold: BigNumber
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
  constructor(
    token0: string,
    token1: string,
    pair: string,
    // kLast: BigNumber,
    isMitigationEnabled: boolean,
    priceToleranceThreshold: BigNumber,
    // poolContract: Contract,
    systemFeeRate: BigNumber,
    isSecurityPool: boolean,
    chainId: number
  ) {
    //  attach all addresses
    this.token0 = token0
    this.token1 = token1
    this.pair = pair

    //  attach contract, request if pool is security one, get latest known reserves
    // this.poolContract = poolContract
    this.isSecurityPool = isSecurityPool
    if (!isSecurityPool) {
      this.checkIfSecurity()
    }

    // this.updateReserves()

    //  get latest k-coefficient value, mitigation status, tolerance threshold
    // this.kLast = kLast
    this.isMitigationEnabled = isMitigationEnabled
    this.priceToleranceThreshold = priceToleranceThreshold
    this.systemFeeRate = systemFeeRate
    this.chainId = chainId


    // ! IMPORTANT: make sure that there will be boolean value at moment, not 'promise' one
    if (this.isSecurityPool) {
      this.checkIfToken0Sec()
      this.checkIfToken1Sec()
    }
  }

  /**
   * verify out values, slippage, liquidity and mitigation check of the swap transaction
   * @param transaction swap transaction verification of which is required
   * @param contract
   * @param isSecurity check if a
   */

  async verifySwap(transaction: Swap, isSecurity: boolean) {
    if (!this.chainId) return

    const canConsult = await this.canConsultOracle(transaction) //(FACTORY_CONTRACT)

    if (canConsult) {
      await this.consultOracle(transaction) //(FACTORY_CONTRACT)
    }

    //  perform initial tranasaction values verification and slippage check
    this.verifyOutValues(transaction)
    // this.verifySlippage(transaction) //need disc

    //  find current out values with system fees
    const amount0OutWithSystemFee: BigNumber = this.isToken0Sec
      ? transaction.amount0Out
      : transaction.amount0Out.add(transaction.amount0Out.mul(this.systemFeeRate).div(1000))
    const amount1OutWithSystemFee: BigNumber = this.isToken1Sec
      ? transaction.amount1Out
      : transaction.amount1Out.add(transaction.amount1Out.mul(this.systemFeeRate).div(1000))

    //  ensure that reserves are bigger than out values
    if (!this.reserve0?.gt(amount0OutWithSystemFee)) {
      throw new Error('Reserve has insufficient liquidity')
    }

    if (!this.reserve1?.gt(amount1OutWithSystemFee)) {
      throw new Error('Reserve has insufficient liquidity')
    }

    //  set final reserves value by extracting out value with fees
    const reserve0Final = this.reserve0.sub(amount0OutWithSystemFee)
    const reserve1Final = this.reserve1.sub(amount1OutWithSystemFee)

    /*  perform mitigation check if such property is attached to the current pool and 
    it is possible to consult Oracle at the moment */
    if (this.isMitigationEnabled && this.isConsultable && reserve0Final && reserve1Final) {
      return this.verifyMitigation(transaction, reserve0Final, reserve1Final)
    }
  }

  /**
   * update current pool reserves via requesting current reserves values through contract
   */
  async updateReserves(reserve0:BigNumber, reserve1:BigNumber) {
    // const record = await this.poolContract.methods.getReserves().call()
    this.reserve0 = reserve0
    this.reserve1 = reserve1 //bigNumber
  }

  /**
   * ! IMPORTANT: set Oracle responses to the specified variables of amount0Out and amount1Out
   * get Oracle estimated out values (only for those that have not-zero in values)
   * @param contract factory contract to perform request to Oracle
   * @param transaction swap transaction for which it is required to perform check
   */
  async consultOracle(transaction: Swap) {
    if (transaction.amount0In.gt(0)) {
    //   const response = await contract.methods.oracleConsult(this.token0, transaction.amount0In, this.token1).call()
      transaction.oracleAmount1Out = transaction.oracleAmount1Out
    } else {
      transaction.oracleAmount1Out = transaction.oracleAmount1Out
    }
    if (transaction.amount1In.gt(0)) {
    //   const response = await contract.methods.oracleConsult(this.token1, transaction.amount1In, this.token0).call()
      transaction.oracleAmount0Out = transaction.oracleAmount0Out
    } else {
      transaction.oracleAmount0Out = transaction.oracleAmount0Out
    }
  }

  /**
   * request via contract if it is possible to consult Oracle, set response to inner flag
   * @param contract factory contract for performing Oracle request
   */
  async canConsultOracle(tranasaction: Swap) {
    const response = ((tranasaction.oracleAmount0Out !== undefined) && (tranasaction.oracleAmount1Out !== undefined)) // await contract.methods.oracleCanConsult(this.token0, this.token1).call()
    this.isConsultable = response
    return response
  }

  /**
   * Check if current pool is the security one
   * @param contract pool contract to request if it is security
   */
  async checkIfSecurity() {
    // const response = await this.poolContract.methods.isSecurityPool().call()
    this.isSecurityPool = true
  }

  /**
   * check if token 0 is a security one
   */
  async checkIfToken0Sec() {
    this.isToken0Sec = true
  }

  /**
   * check if token 1 is a security one
   */
  async checkIfToken1Sec() {
    this.isToken1Sec = false
  }

  /**
   * check if out values are valid
   * @param transaction swap-operation values of which is required to verify
   */
  verifyOutValues(transaction: Swap) {
    if (!(transaction.amount0Out.gt(0) || transaction.amount1Out.gt(0))) {
      throw new Error(`Transaction has insufficient output amount`)
    }

    if (
      !(
        this.reserve0 &&
        this.reserve1 &&
        transaction.amount0Out.lt(this.reserve0) &&
        transaction.amount1Out.lt(this.reserve1)
      )
    ) {
      throw new Error(`Reserve has insufficient liquidity`)
    }

    if (!(transaction.to != this.token0 && transaction.to != this.token1)) {
      throw new Error(`Invalid sender address`)
    }
  }

  /**
   * check transaction slippage
   * @param transaction swap transaction that requires verification
   */
  verifySlippage(transaction: Swap) {
    //  calculate values with fees
    const amount0InWithFee: BigNumber = transaction.amount0In.mul(this.isSecurityPool ? 990 : 997)
    const amount1InWithFee: BigNumber = transaction.amount1In.mul(this.isSecurityPool ? 990 : 997)

    if (!this.reserve0 || !this.reserve1) {
      throw new Error('Reserves not provided')
    }

    const amount0OutMin: BigNumber = amount1InWithFee
      .mul(this.reserve0.mul(BigNumber.from(1000).sub(utils.parseUnits(`${transaction.slope}`))))
      .div(this.reserve1.mul(1000).mul(1000).add(amount0InWithFee))

    const amount1OutMin: BigNumber = amount0InWithFee
      .mul(this.reserve1.mul(BigNumber.from(1000).sub(utils.parseUnits(`${transaction.slope}`))))
      .div(this.reserve0.mul(1000).mul(1000).add(amount1InWithFee))

    if (!(transaction.amount0Out.lt(amount0OutMin) || transaction.amount0Out.eq(amount0OutMin))) {
      throw new Error(`Max slippage exceeded`)
    }

    if (!(transaction.amount1Out.lt(amount1OutMin) || transaction.amount1Out.eq(amount1OutMin))) {
      throw new Error(`Max slippage exceeded`)
    }
  }

  /**
   * perform transaction mitigation verification
   * @param transaction swap operation to check
   * @param reserve0Final token 0 final reserve after extracting out value with fee
   * @param reserve1Final token 1 final reserve after extracting out value with fee
   */
  verifyMitigation(transaction: Swap, reserve0Final: BigNumber, reserve1Final: BigNumber) {
    // console.log("Inside verify mitigation")
    // console.log(transaction.amount0In.toString(), transaction.amount0Out.toString())
    // console.log(transaction.amount1In.toString(), transaction.amount1Out.toString())
    // console.log(transaction.oracleAmount0Out.toString(), transaction.oracleAmount1Out.toString())
    // console.log(reserve0Final.toString(), reserve1Final.toString())
    if (!transaction.oracleAmount0Out || !transaction.oracleAmount1Out) {
      throw new Error()
    }

    //  find slice factors
    const sliceFactor0: BigNumber = this.calculateSliceFactor(reserve0Final, transaction.amount0Out)
    const sliceFactor1: BigNumber = this.calculateSliceFactor(reserve1Final, transaction.amount1Out)

    //  set difference between out values and oracle estimations, check them to be bigger or equal to 0
    const out0AmountDiff: BigNumber = this.estimateAmountDifference(
      transaction.oracleAmount0Out,
      transaction.amount0Out
    )
    const out1AmountDiff: BigNumber = this.estimateAmountDifference(
      transaction.oracleAmount1Out,
      transaction.amount1Out
    )
    if (!(out0AmountDiff.gte(0) || transaction.amount1In.eq(0))) {
      throw new Error(`Out value is smaller or equal to zero`)
    }

    if (!(out1AmountDiff.gte(0) || transaction.amount0In.eq(0))) {
      throw new Error(`Out value is smaller or equal to zero`)
    }

    //  find slice factor curve for each token

    //const testSliceFactor1 = BigNumber.from('101')

    let sliceFactor0Curve: BigNumber = sliceFactor0.mul(this.sqrt(sliceFactor0))
    let sliceFactor1Curve: BigNumber = sliceFactor1.mul(this.sqrt(sliceFactor1))
    sliceFactor0Curve = sliceFactor0Curve.gt(this.priceToleranceThreshold)
      ? this.priceToleranceThreshold
      : sliceFactor0Curve
    sliceFactor1Curve = sliceFactor1Curve.gt(this.priceToleranceThreshold)
      ? this.priceToleranceThreshold
      : sliceFactor1Curve


    // console.log(sliceFactor0Curve.toString(), sliceFactor1Curve.toString())
    // console.log(out0AmountDiff.toString(), out1AmountDiff.toString())

    /*  transaction is valid if transaction out value has acceptable difference from Oracle estimation
    or other side incoming value is 0 (therefore, out value will be 0)  */
    if (!(out0AmountDiff.lte(BigNumber.from(100).sub(sliceFactor0Curve)) || transaction.amount1In.eq(0))) {
      // throw new Error(`Mitigation0 ${transaction.id}: OUT_VALUE_TOO_FAR_FROM_ORACLE`)
      throw new Error(`Out value too far from Oracle, your current value x, but from y to z could pass`)
    }

    if (!(out1AmountDiff.lte(BigNumber.from(100).sub(sliceFactor1Curve)) || transaction.amount0In.eq(0))) {
      // throw new Error(`Mitigation1 ${transaction.id}: OUT_VALUE_TOO_FAR_FROM_ORACLE`)
      throw new Error(`Out value too far from Oracle`)
    }

    return true
  }

  /**
   * find a slice factor for token considering current reserves and transaction out value
   * @param reserve token reserve
   * @param transactionOutAmount transaction out value for respective token
   * @returns slice factor
   */
  calculateSliceFactor(reserve: BigNumber, transactionOutAmount: BigNumber): BigNumber {
    if (reserve.gt(transactionOutAmount)) {
      return BigNumber.from(100).sub(BigNumber.from(100).mul(reserve.sub(transactionOutAmount)).div(reserve))
    } else {
      return BigNumber.from(100)
    }
  }

  /**
   * find difference between Oracle and transaction out values
   * @param oracleAmountOut Oracle estimated out value
   * @param transactionAmountOut transaction estimated out value
   * @returns amount difference between Oracle and transaction estimations
   */
  estimateAmountDifference(oracleAmountOut: BigNumber, transactionAmountOut: BigNumber): BigNumber {
    if (oracleAmountOut.eq(transactionAmountOut)) {
      return BigNumber.from(0)
    } else {
      const biggerAmount: BigNumber = this.max(transactionAmountOut, oracleAmountOut)
      const smallerAmount: BigNumber = this.min(transactionAmountOut, oracleAmountOut)
      return BigNumber.from(100).mul(biggerAmount.sub(smallerAmount)).div(biggerAmount.add(smallerAmount).div(2))
    }
  }

  /**
   * get smallest number out of two given
   * @param first first number
   * @param second second number
   * @returns smallest of two numbers
   */
  min(first: BigNumber, second: BigNumber): BigNumber {
    return first.lt(second) ? first : second
  }

  /**
   * get biggest number out of two given
   * @param first first number
   * @param second second number
   * @returns biggest of two numbers
   */
  max(first: BigNumber, second: BigNumber): BigNumber {
    return first.gt(second) ? first : second
  }

  /**
   * calculate square root of given BigNumber
   * @param value value for which square root is required to find
   * @returns square root of given BigNumber
   */
  sqrt(value: BigNumber): BigNumber {
    const x: BigNumber = value
    let z: BigNumber = x.add(this.ONE).div(this.TWO)
    let y: BigNumber = x

    while (z.sub(y).lt(0)) {
      //  check value not to be negative
      y = z
      z = x.div(z).add(z).div(this.TWO)
    }
    return y
  }
}

interface VerifyOptions {
  token0: string
  token1: string

  pair: string

//   kLast: string | BigNumber

  priceToleranceThreshold: BigNumber
  systemFeeRate: BigNumber

  id: string

  amountInFrom?: BigNumber
  amountInTo?: BigNumber

  amountOutFrom?: BigNumber
  amountOutTo?: BigNumber

  sender?: string
  receiver?: string

  slope: number

  isSecurity: boolean
  pairAddress: string
  chainId: number

  //isToken0Sec: boolean
  //isToken1Sec: boolean
}


function createPool(options:VerifyOptions) {
    const pool = new Pool(
        options.token0,
        options.token1,
        options.pair,
        true,
        options.priceToleranceThreshold,
        options.systemFeeRate,
        true,
        -1
      )

    return pool;
}

function getAmountOut(amountIn: BigNumber, reserveIn:BigNumber, reserveOut:BigNumber) {
    let amountInWithFee = amountIn.mul(990)
    let numerator = amountInWithFee.mul(reserveOut)
    let denominator = reserveIn.mul(1000).add(amountInWithFee) 
    let amountOut = numerator.div(denominator)

    return amountOut
}


async function verifySwap(balance0: BigNumber, balance1: BigNumber, tokenIn: string, tokenOut: string, amountIn: BigNumber, oracleAmountOut?: BigNumber) {
    let reserveIn:BigNumber, reserveOut: BigNumber;
    let amount0In:BigNumber, amount1In:BigNumber, amount0Out:BigNumber, amount1Out:BigNumber;
    let oracleAmount0Out: BigNumber|undefined, oracleAmount1Out:BigNumber|undefined;

    // if tokenIn == 'X'  
    reserveIn = balance0;
    reserveOut = balance1;
    amount0In = amountIn;
    amount1In = BigNumber.from(0);
    amount0Out = BigNumber.from(0);
    amount1Out = getAmountOut(amountIn, reserveIn, reserveOut)
    oracleAmount0Out = BigNumber.from(0);
    oracleAmount1Out = oracleAmountOut;
    
    if (tokenIn == 'Y') {
        reserveIn = balance1;
        reserveOut = balance0;
        amount0In = BigNumber.from(0);
        amount1In = amountIn;
        amount0Out = getAmountOut(amountIn, reserveIn, reserveOut)
        amount1Out = BigNumber.from(0);
        oracleAmount0Out = oracleAmountOut
        oracleAmount1Out = BigNumber.from(0);
    }

    let transaction = new Swap("id", amount0In, amount1In, amount0Out, amount1Out, oracleAmount0Out, oracleAmount1Out, "sender", "to", 0.05, -1)
    pool.updateReserves(balance0, balance1)
    
    try {
        const result = await pool.verifySwap(transaction, true)
        console.log('{ status: "success" }')
    } catch (e: any) {
        console.log(`{ status: "failure", message: "${e.message}"}`)
        return
    }
}


async function check_transaction(
  balance0: string, 
  balance1: string,
  tokenIn: string,
  tokenOut: string,
  amountIn: string,
  amountOut: string,
  oracleOut: string
) {
  let pool = createPool({
    token0: "ELON", 
    token1: "WETH",
    pair: 'pair_address',
    priceToleranceThreshold: BigNumber.from(98),
    systemFeeRate: BigNumber.from(true ? 4 : 0),
    id: `swap-${Math.floor(1 + Math.random() * 100000000)}`,
    slope: 0.5,
    isSecurity: true,
    pairAddress: 'pair',
    chainId: -1
  })

  let reserve0 = BigNumber.from(balance0)
  let reserve1 = BigNumber.from(balance1)

  let amount0In = null
  let amount1In = null
  let amount0Out = null
  let amount1Out = null
  let oracleAmount0Out = null
  let oracleAmount1Out = null

  
  if (tokenIn == pool.token0) {
    amount0In = BigNumber.from(amountIn)
    amount1In = BigNumber.from(0)
    amount0Out = BigNumber.from(0)
    amount1Out = BigNumber.from(amountOut)
    oracleAmount0Out = BigNumber.from(0)
    oracleAmount1Out = BigNumber.from(oracleOut)
  } else {
    amount0In = BigNumber.from(0)
    amount1In = BigNumber.from(amountIn)
    amount0Out = BigNumber.from(amountOut)
    amount1Out = BigNumber.from(0)
    oracleAmount0Out = BigNumber.from(oracleOut)
    oracleAmount1Out = BigNumber.from(0)
  }

  // form a transaction and update reserves
  let transaction = new Swap(
    "id", amount0In, amount1In, amount0Out, amount1Out, 
    oracleAmount0Out, oracleAmount1Out, "sender", "to", 0.05, -1
  )
  pool.updateReserves(reserve0, reserve1)

  try {
    const result = await pool.verifySwap(transaction, true)
    console.log("success")
} catch (e) {
    console.log(e)
    return
}
}


async function main()  {
    let initialReservesList = [5500, 30000, 75000, 150000, 300000, 750000]
    let diffList = [-50, -20, -10, 0, 10, 20]

    let pool = createPool({
        token0: 'X', 
        token1: 'Y',
        pair: 'pair_address',
        priceToleranceThreshold: BigNumber.from(98),
        systemFeeRate: BigNumber.from(true ? 10 : 3),
        id: `swap-${Math.floor(1 + Math.random() * 100000000)}`,
        slope: 0.5,
        isSecurity: true,
        pairAddress: 'pair',
        chainId: -1
    })

    for (let initialReserve of initialReservesList) {
        for (let diff of diffList) {
            for (let i = 1; i < initialReserve; i++) {
                let reserve0 = BigNumber.from(initialReserve).mul('1000000000000000000')
                let reserve1 = BigNumber.from(initialReserve).mul('1000000000000000000')

                let amount1In = BigNumber.from(i).mul('1000000000000000000');
                let amount0Out = getAmountOut(amount1In, reserve1, reserve0)
                let oracleAmount0Out = amount0Out.mul(100).div(100 + diff)
                // console.log("initialReserve", initialReserve)

                let transaction = new Swap("id", BigNumber.from(0), amount1In, amount0Out, BigNumber.from(0), oracleAmount0Out, BigNumber.from(0), "sender", "to", 0.05, -1)
                pool.updateReserves(reserve0, reserve1)
                
                try {
                    const result = await pool.verifySwap(transaction, true)
                    // console.log('success')
                } catch (e) {
                    console.log(i)
                    // console.log(amount0Out.toString())
                    // console.log(oracleAmount0Out.toString())
                    console.log(e)
                    return
                }
            }
        }
    }
}

let pool = createPool({
    token0: 'X', 
    token1: 'Y',
    pair: 'pair_address',
    priceToleranceThreshold: BigNumber.from(98),
    systemFeeRate: BigNumber.from(true ? 10 : 3),
    id: `swap-${Math.floor(1 + Math.random() * 100000000)}`,
    slope: 0.5,
    isSecurity: true,
    pairAddress: 'pair',
    chainId: -1
})

interface MitigationArguments{
  balance_0: string;
  balance_1: string;
  tokenIn: string;
  tokenOut: string;
  amountIn: string;
  amountOut: string;
  oracleOut: string;
}

export const args = parse<MitigationArguments>({
      balance_0: { type: String, description: "balance of token 0", optional: true },
      balance_1: { type: String, description: "balance of token 1", optional: true },
      tokenIn: { type: String, description: "address/name of incoming token", optional: true },
      tokenOut: { type: String, description: "address/name of outcoming token", optional: true },
      amountIn: { type: String, description: "amount of incoming token to exchange", optional: true },
      amountOut: { type: String, description: "amount of outgoing token to get for exchange", optional: true },
      oracleOut: { type: String, description: "amount of out token conform Oracle TWAP", optional: true },
})

check_transaction(
  args.balance_0, args.balance_1, args.tokenIn, args.tokenOut, args.amountIn, args.amountOut, args.oracleOut
)