var SafeMathLib = artifacts.require("SafeMathLib");
var CrowdsaleToken = artifacts.require("CrowdsaleToken");
var MultiSigWallet = artifacts.require("MultiSigWallet")
var FlatPricing = artifacts.require("FlatPricing")
var AllocatedCrowdsale = artifacts.require("AllocatedCrowdsale")
var DefaultFinalizeAgent = artifacts.require("DefaultFinalizeAgent")

module.exports = function (deployer) {
    var _deployAddress = "0xA06b548d954Fa504e54BCCAD8f7F58361d8949E4";
    // who own invested ETH
    var _walletAccounts = [_deployAddress]
    var _walletRequired = 1
    // who own all tokens
    var _beneficiary = _deployAddress
    var _name = "BitHeroToken";
    var _symbol = "BTH";
    var _totalSupply = 10 ** 9 * 10 ** 18;
    var _decimals = 18;
    // in js, month start from 0, day start from 1.
    var _start = new Date(2018, 7, 1, 0, 0).getTime() / 1000;
    var _end = new Date(2019, 7, 1, 0, 0).getTime() / 1000;
    var _minimumFundingGoal = 0;
    deployer.deploy(SafeMathLib);
    deployer.link(SafeMathLib, [CrowdsaleToken, FlatPricing, AllocatedCrowdsale]);
    deployer.deploy([
        [MultiSigWallet, _walletAccounts, _walletRequired],
        [CrowdsaleToken, _name, _symbol, _totalSupply, _decimals, false],
        [FlatPricing, 1.5*10**14]
    ]).then(function () {
        return deployer.deploy(AllocatedCrowdsale, CrowdsaleToken.address, FlatPricing.address, MultiSigWallet.address, _start, _end, _minimumFundingGoal, _beneficiary);
    }).then(function () {
        return deployer.deploy(DefaultFinalizeAgent, CrowdsaleToken.address, AllocatedCrowdsale.address);
    });
};
