var CrowdsaleToken = artifacts.require("CrowdsaleToken");
var MultiSigWallet = artifacts.require("MultiSigWallet")
var AllocatedCrowdsale = artifacts.require("AllocatedCrowdsale")
var DefaultFinalizeAgent = artifacts.require("DefaultFinalizeAgent")

module.exports = function (deployer) {
    var _deployAddress = "0xA06b548d954Fa504e54BCCAD8f7F58361d8949E4";
    var _beneficiary = _deployAddress
    var _publicSupply = 6.25 * 10**7 * 10**18;
    CrowdsaleToken.deployed().then(function (instance) {
        token = instance;
        token.approve(AllocatedCrowdsale.address, _publicSupply);
        token.setTransferAgent(MultiSigWallet.address, true);
        token.setTransferAgent(AllocatedCrowdsale.address, true);
        token.setTransferAgent(DefaultFinalizeAgent.address, true);
        token.setTransferAgent(_beneficiary, true);

        token.setReleaseAgent(DefaultFinalizeAgent.address);
        token.setUpgradeMaster(MultiSigWallet.address);
    });

    AllocatedCrowdsale.deployed().then(function (instance) {
        crowdsale = instance;
        return crowdsale.setFinalizeAgent(DefaultFinalizeAgent.address)
    });
};