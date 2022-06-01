/* eslint-disable @typescript-eslint/no-var-requires */
import { FACTORY_ROUTER_ADDRESS } from 'constants/addresses'
import { BigNumber, utils } from 'ethers'
import { useActiveWeb3React } from 'hooks/web3'
import { Contract } from 'web3-eth-contract'


//  -----------------------------------------     PARAMETERS, CONSTANTS   ------------------------------------------------------------------


// abis
let PERIPHERY_LP_ABI = require('abis/IxsV2LiquidityRouter.json')
PERIPHERY_LP_ABI = PERIPHERY_LP_ABI.abi

let SWAP_ROUTER_ABI = require('abis/IxsV2SwapRouter.json')
SWAP_ROUTER_ABI = SWAP_ROUTER_ABI.abi

let FACTORY_ABI = require('abis/IxsV2Factory.json')
FACTORY_ABI = FACTORY_ABI.abi

let PAIR_ABI = require('abis/IxsV2Pair.json')
PAIR_ABI = PAIR_ABI.abi

let ERC20_FAUCET_ABI = require('abis/Erc20Custom.json')
ERC20_FAUCET_ABI = ERC20_FAUCET_ABI.abi

const Web3Global = require('web3')


class Web3 {
  getUrl(chainId: number): any {
    const networkNames = {
      '1': 'homestead',
      '42': 'kovan',
      '137': 'matic',
      '80001': 'maticmum',
    } as Record<string, string>

    let host = ''
    switch (networkNames[chainId.toString()]) {
      case 'homestead':
        host = 'mainnet.infura.io'
        break
      case 'kovan':
        host = 'kovan.infura.io'
        break
      case 'matic':
        host = 'polygon-mainnet.infura.io'
        break
      case 'maticmum':
        host = 'polygon-mumbai.infura.io'
        break
      default:
        break
    }

    return new Web3Global(`https://${host}/v3/${process.env.REACT_APP_INFURA_KEY}`)
  }
}



//    --------------------------------------------    MITIGATION REALIZATION SECTION  ---------------------------------------------------

class Swap {
  /*
    Swap transaction class, remember that token0 and token1 are representing hash addresses of the tokens
  in the pool. Numerical index of the token depends on the pool name, meaning that in case of pool "WBTC/USDC"
  token0 will be WBTC and token1 will be USDC, while in case of "ELON/WETH" token 0 will be ELON and token1
  will be WETH

  Description of fields:
    id -               hash identificator of the transaction
    amount0In -        how many tokens of token0 are requested to exchange
    amount1In -        how many tokens of token1 are requested to exchange
    amount0Out -       how many tokens of token0 will user get in exchange
    amount1Out -       how many tokens of token1 will user get in exchange
    oracleAmount0Out - how many tokens of token0 should user get conform TWAP (time-weighted average price) of Oracle
    oracleAmount1Out - how many tokens of token1 should user get conform TWAP of Oracle
    chainID -          web3 network id (kovan, matic and etc.)
  */
  id: string
  amount0In: BigNumber
  amount1In: BigNumber
  amount0Out: BigNumber
  amount1Out: BigNumber
  oracleAmount0Out: BigNumber | undefined
  oracleAmount1Out: BigNumber | undefined
  chainId: number

  constructor(
    id: string,
    amount0In: BigNumber,
    amount1In: BigNumber,
    amount0Out: BigNumber,
    amount1Out: BigNumber,
    chainId: number
  ) {
    this.id = id
    this.amount0In = amount0In
    this.amount1In = amount1In
    this.amount0Out = amount0Out
    this.amount1Out = amount1Out
    this.chainId = chainId
  }
}

class Pool {
  /*
    Class used to define all required properties of the pool

  Description of fields:
    token0 -                  hash address of the token0 in pool
    token1 -                  hash address of the token1 in pool
    pair -                    hash address of the pair (pool)
    reserve0 -                how many tokens of token0 are right now in the pool
    reserve1 -                how many tokens of token1 are right now in the pool
    systemFeeRate -           rate of fee collected by the system from the transaction
    isSecurityPool -          does this pool contain security tokens or not
    isToken0Sec -             is token0 a security one or not
    isToken1Sec -             is token1 a security one or not
    chainId -                 web3 network id (kovan, matic and etc.)
    isConsultable -           is it possible to request TWAP from Oracle at current moment. It is required to check everytime
                              because TWAP (time-weighted average price) is calculated based on the prices of the last 24-hours
                              transactions. If there are not enought transactions to perform TWAP estimation then it will not
                              be possible to get TWAP and therefore will not be possible to check the current transaction to 
                              meet TWAP conditions
    ONE -                     constant required for performing square root calculation in a BigNumber logic. The problem is that
                              ethers.BigNumber does not contain at all any method to perform square root calculation and therefore
                              was made a custom implementation
    TWO -                     constant required for performing square root calculation in a BigNumber logic
    priceToleranceThreshold - constant value in percents (example, 98), which defines how far in percents can price of the current
                              transaction differ from the Oracle TWAP one. Algorithm finds in percents how far from the Oracle TWAP
                              price is the current transaction price and if it passes this threshold - then transaction will be aborted
    isMitigationEnabled -     is mitigation enabled for the current pool or not. In case if not - there is no need in mitigation check
    poolContact -             contract that was set for this pool (for performing pool related blockchain requests)
  */
  token0: string
  token1: string
  pair: string

  reserve0?: BigNumber
  reserve1?: BigNumber

  systemFeeRate: BigNumber

  isSecurityPool?: boolean
  isToken0Sec?: boolean
  isToken1Sec?: boolean
  chainId: number

  isConsultable?: boolean

  isMitigationEnabled: boolean

  ONE: BigNumber = BigNumber.from(1)
  TWO: BigNumber = BigNumber.from(2)

  priceToleranceThreshold: BigNumber
  poolContract: Contract

  /**
   * make a pool entity
   * @param token0 first token address
   * @param token1 second token address
   * @param pair pair address
   * @param isMitigationEnabled true if mitigation is enabled, false if not
   * @param priceToleranceThreshold threshold of acceptable difference between transaction out value and Oracle value, for example if to
   *                                this parameter is sent value 98, then as acceptable threshold is considered 2% difference
   * @param systemFeeRate fee rate for operations on this pool
   * @param isSecurityPool flag if this pool is a security one
   * @param poolContract pool contract to request blockchain info about pool
   */
  constructor(
    token0: string,
    token1: string,
    pair: string,
    isMitigationEnabled: boolean,
    priceToleranceThreshold: BigNumber,
    systemFeeRate: BigNumber,
    isSecurityPool: boolean,
    chainId: number,
    poolContract: Contract
  ) {
    //  set addresses
    this.token0 = token0
    this.token1 = token1
    this.pair = pair

    //  set if this pool is security and update current pool reserves
    this.isSecurityPool = isSecurityPool

    this.isMitigationEnabled = isMitigationEnabled
    this.priceToleranceThreshold = priceToleranceThreshold
    this.systemFeeRate = systemFeeRate
    this.chainId = chainId

    //  if this is a security pool, then check which token is a security one
    if (this.isSecurityPool) {
      this.checkIfToken0Sec()
      this.checkIfToken1Sec()
    }
    this.poolContract = poolContract
  }

  /**
   * verify swap to be with correct values, not to break liquidity and to pass mitigation
   * @param transaction swap to verify
   */

  async verifySwap(transaction: Swap) {
    if (!this.chainId) return

    const web3 = new Web3().getUrl(this.chainId)

    const FACTORY = web3.utils.toChecksumAddress(FACTORY_ROUTER_ADDRESS[this.chainId])
    const FACTORY_CONTRACT = new web3.eth.Contract(FACTORY_ABI, FACTORY) //  contract to consult oracle

    const isMitigationEnabledLocally = await this.poolContract.methods.mitigationEnabled().call()
    if (!isMitigationEnabledLocally) return

    //  while TWAP was not requested, set variables to be 0
    transaction.oracleAmount1Out = BigNumber.from(0)
    transaction.oracleAmount0Out = BigNumber.from(0)
    await this.updateReserves()

    //  perform initial tranasaction values verification
    this.verifyOutValues(transaction)

    //  check if it is possible to consult with TWAP and if it is - request TWAP
    const canConsult = await this.canConsultOracle(FACTORY_CONTRACT) //(FACTORY_CONTRACT)
    if (canConsult) {
      await this.consultOracle(FACTORY_CONTRACT, transaction) //(FACTORY_CONTRACT)
    }

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
    const reserve0Final = this.reserve0?.sub(amount0OutWithSystemFee)
    const reserve1Final = this.reserve1?.sub(amount1OutWithSystemFee)

    /*  perform mitigation check if such property is attached to the current pool and 
    it is possible to consult Oracle at the moment */
    if (this.isMitigationEnabled && this.isConsultable && reserve0Final && reserve1Final) {
      this.verifyMitigation(transaction, reserve0Final, reserve1Final)
    }
  }

  /**
   * request current pool reserves using blockchain contract
   */
  async updateReserves() {
    const record = await this.poolContract.methods.getReserves().call()
    this.reserve0 = BigNumber.from(record['_reserve0'])
    this.reserve1 = BigNumber.from(record['_reserve1'])
  }

  /**
   * ! IMPORTANT: set Oracle responses to the specified variables of amount0Out and amount1Out
   * get Oracle estimated out values (only for those that have not-zero in values)
   * @param contract factory contract to perform request to Oracle
   * @param transaction swap transaction for which it is required to perform check
   */
  async consultOracle(contract: Contract, transaction: Swap) {
    if (transaction.amount0In.gt(0)) {
      const response = await contract.methods.oracleConsult(this.token0, transaction.amount0In, this.token1).call()
      transaction.oracleAmount1Out = BigNumber.from(response)
    } else {
      transaction.oracleAmount1Out = BigNumber.from(0)
    }
    if (transaction.amount1In.gt(0)) {
      const response = await contract.methods.oracleConsult(this.token1, transaction.amount1In, this.token0).call()
      transaction.oracleAmount0Out = BigNumber.from(response)
    } else {
      transaction.oracleAmount0Out = BigNumber.from(0)
    }
  }

  /**
   * request via contract if it is possible to consult Oracle, set response to inner flag
   * @param contract factory contract for performing Oracle request
   */
  async canConsultOracle(contract: Contract) {
    const response = await contract.methods.oracleCanConsult(this.token0, this.token1).call()
    this.isConsultable = response
    return response
  }

  /**
   * check if token 0 is a security one
   */
  async checkIfToken0Sec() {
    const response = await this.poolContract.methods.isToken0Sec().call()
    this.isToken0Sec = response
  }

  /**
   * check if token 1 is a security one
   */
  async checkIfToken1Sec() {
    const response = await this.poolContract.methods.isToken1Sec().call()
    this.isToken1Sec = response
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
  }


  /**
   * perform transaction mitigation verification
   * @param transaction swap operation to check
   * @param reserve0Final token 0 final reserve after extracting out value with fee
   * @param reserve1Final token 1 final reserve after extracting out value with fee
   */
  verifyMitigation(transaction: Swap, reserve0Final: BigNumber, reserve1Final: BigNumber) {
    // check if there is any TWAP to consult with
    if (transaction.oracleAmount0Out.eq(0) && transaction.oracleAmount1Out.eq(0)) {
      throw new Error('No TWAP, but mitigation called')
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
    let sliceFactor0Curve: BigNumber = sliceFactor0.mul(this.sqrt(sliceFactor0))
    let sliceFactor1Curve: BigNumber = sliceFactor1.mul(this.sqrt(sliceFactor1))
    sliceFactor0Curve = sliceFactor0Curve.gt(this.priceToleranceThreshold)
      ? this.priceToleranceThreshold
      : sliceFactor0Curve
    sliceFactor1Curve = sliceFactor1Curve.gt(this.priceToleranceThreshold)
      ? this.priceToleranceThreshold
      : sliceFactor1Curve

    /*  transaction is valid if transaction out value has acceptable difference from Oracle estimation
    or other side incoming value is 0 (therefore, out value will be 0)  */
    if (!(out0AmountDiff.lte(BigNumber.from(100).sub(sliceFactor0Curve)) || transaction.amount1In.eq(0))) {
      throw new Error(`Out value too far from Oracle`)
    }
    if (!(out1AmountDiff.lte(BigNumber.from(100).sub(sliceFactor1Curve)) || transaction.amount0In.eq(0))) {
      throw new Error(`Out value too far from Oracle`)
    }
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


//  ---------------------------------------------   MITIGATION VERIFICATION CALL SECTION  ---------------------------------------------------
//                                      HOW TO CALL MITIGATION SCRIPT VERIFICATION OF THE TRANSACTION



interface VerifyOptions {
  token0: string
  token1: string
  pair: string

  isMitigationEnabled: boolean
  priceToleranceThreshold: BigNumber
  systemFeeRate: BigNumber
  isSecurity: boolean
  chaidId: number

  id: string
  amount0In: BigNumber
  amount1In: BigNumber
  amount0Out: BigNumber
  amount1Out: BigNumber

  chainId: number
  poolContract: Contract
}

export async function verifySwap(options: VerifyOptions) {
  const web3 = new Web3().getUrl(options.chainId)
  const poolAddress = web3.utils.toChecksumAddress(options.pair)
  const POOL_CONTRACT = new web3.eth.Contract(PAIR_ABI, poolAddress)

  const pool = new Pool(
    options.token0,
    options.token1,
    options.pair,
    options.isMitigationEnabled,
    options.priceToleranceThreshold,
    options.systemFeeRate,
    options.isSecurity,
    options.chaidId,
    POOL_CONTRACT
  )

  const transaction = new Swap(
    options.id,
    options.amount0In,
    options.amount1In,
    options.amount0Out,
    options.amount1Out,
    options.chainId
  )

  await pool.verifySwap(transaction)
}