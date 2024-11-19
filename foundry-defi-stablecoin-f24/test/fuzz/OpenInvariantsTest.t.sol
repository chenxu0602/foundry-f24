// SPDX-License-Identifier: MIT
pragma solidity >=0.8.19 <0.9.0;

import {Test, console} from "forge-std/Test.sol";
import {StdInvariant} from "forge-std/StdInvariant.sol";
import {DeployDSC} from "../../script/DeployDSC.s.sol";
import {DSCEngine} from "../../src/DSCEngine.sol";
import {DecentralizedStableCoin} from "../../src/DecentralizedStableCoin.sol";
import {HelperConfig} from "../../script/HelperConfig.s.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";


contract OpenInvariantsTest is StdInvariant, Test {
    DeployDSC public deployer;
    DSCEngine public dsce;
    DecentralizedStableCoin public dsc;
    HelperConfig public config;
    address public weth;
    address public wbtc;

    function setUp() external {
        deployer = new DeployDSC();
        (dsc, dsce, config) = deployer.run();
        (,, weth, wbtc,) = config.activeNetworkConfig();
        require(weth != address(0), "Invalid WETH address");
        require(wbtc != address(0), "Invalid WBTC address");
        console.log("address of dsce: ", address(dsce));
        targetContract(address(dsce));
        console.log("Done setting up.");
        console.log("Address of DSCEngine: ", address(dsce));
        console.log("Address of DecentralizedStableCoin: ", address(dsc));

    }

    function invariant_OpenProtocolMustHaveMoreValueThanTotalSupply() public view{
        uint256 totalSupply = dsc.totalSupply();
        console.log("totalSupply", totalSupply);
        uint256 totalWethDeposited = IERC20(weth).balanceOf(address(dsce));
        uint256 totalWbtcDeposited = IERC20(wbtc).balanceOf(address(dsce));

        uint256 wethValue = dsce.getUsdValue(weth, totalWethDeposited);
        uint256 wbtcValue = dsce.getUsdValue(wbtc, totalWbtcDeposited);

        console.log("weth value: ", wethValue);
        console.log("wbtc value: ", wbtcValue);

        assert(wethValue + wbtcValue >= totalSupply);
    }
}