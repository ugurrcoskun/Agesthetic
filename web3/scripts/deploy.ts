import { ethers } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("Deploying contracts with the account:", deployer.address);

  const IntroBounty = await ethers.getContractFactory("IntroBounty");
  const introBounty = await IntroBounty.deploy();

  await introBounty.waitForDeployment();

  const address = await introBounty.getAddress();
  console.log("IntroBounty deployed to:", address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
