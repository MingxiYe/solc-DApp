var SafeMathLib = artifacts.require("SafeMathLib");
var CrowdsaleToken = artifacts.require("CrowdsaleToken");
var MultiSigWallet = artifacts.require("MultiSigWallet")
var FlatPricing = artifacts.require("FlatPricing")
var AllocatedCrowdsale = artifacts.require("AllocatedCrowdsale")
var DefaultFinalizeAgent = artifacts.require("DefaultFinalizeAgent")

module.exports = function (deployer) {
    var _deployAddress = "0x3A0E14268753AA9808aFb69ffc927bf9EDb5Ab97";
    var _beneficiary = "0xAa26FcBE0c0e8f03943B5842fd33655328E16efb"//_deployAddress
    var _walletOwner = ""
    // var _beneficiary = _deployAddress
    // who own invested ETH
    var _walletAccounts = [_walletOwner, _beneficiary]
    var _walletRequired = 2
    // who own all tokens
    var _name = "BitHeroToken";
    var _symbol = "BTH";
    var _totalSupply = 10 ** 9 * 10 ** 18;
    var _decimals = 18;
    // in js, month start from 0, day start from 1.
    var _start = new Date(2018, 8, 1, 0, 0).getTime() / 1000;
    var _end = new Date(2019, 8, 1, 0, 0).getTime() / 1000;
    var _publicSupply = 6.25 * 10 ** 7 * 10 ** 18;
    var _minimumFundingGoal = 0;
    deployer.deploy(SafeMathLib);
    deployer.link(SafeMathLib, [CrowdsaleToken, FlatPricing, AllocatedCrowdsale]);
    deployer.deploy([
        [MultiSigWallet, _walletAccounts, _walletRequired],
        [CrowdsaleToken, _name, _symbol, _totalSupply, _decimals, false, { from: _beneficiary }],
        [FlatPricing, 1.5*10**14]
    ]).then(function () {
        return deployer.deploy(AllocatedCrowdsale, CrowdsaleToken.address, FlatPricing.address, MultiSigWallet.address, _start, _end, _minimumFundingGoal, _beneficiary, {from: _beneficiary});
    }).then(function () {
        return deployer.deploy(DefaultFinalizeAgent, CrowdsaleToken.address, AllocatedCrowdsale.address);
    }).then(function () {
        CrowdsaleToken.deployed().then(function (instance) {
            token = instance;
            token.approve(AllocatedCrowdsale.address, _publicSupply, { from: _beneficiary });
            token.setTransferAgent(MultiSigWallet.address, true, { from: _beneficiary });
            token.setTransferAgent(AllocatedCrowdsale.address, true, { from: _beneficiary });
            token.setTransferAgent(DefaultFinalizeAgent.address, true, { from: _beneficiary });
            token.setTransferAgent(_deployAddress, true, { from: _beneficiary });
            token.setTransferAgent(_beneficiary, true, { from: _beneficiary });

            token.setReleaseAgent(DefaultFinalizeAgent.address, { from: _beneficiary });
            token.setUpgradeMaster(MultiSigWallet.address, { from: _beneficiary });
        });

        AllocatedCrowdsale.deployed().then(function (instance) {
            crowdsale = instance;
            return crowdsale.setFinalizeAgent(DefaultFinalizeAgent.address, { from: _beneficiary });
        });
    });
};
