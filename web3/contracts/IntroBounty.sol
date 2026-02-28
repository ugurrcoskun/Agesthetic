// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract IntroBounty {
    struct Bounty {
        address creator;
        string targetId; // e.g., twitter handle
        uint256 amount;
        bool isActive;
    }

    uint256 public nextBountyId;
    mapping(uint256 => Bounty) public bounties;

    event BountyCreated(uint256 indexed bountyId, address indexed creator, string targetId, uint256 amount);
    event BountyReleased(uint256 indexed bountyId, address indexed introducer, uint256 amount);
    event BountyCancelled(uint256 indexed bountyId, address indexed creator, uint256 amount);

    function createBounty(string memory _targetId) external payable returns (uint256) {
        require(msg.value > 0, "Amount must be greater than 0");

        uint256 bountyId = nextBountyId++;
        bounties[bountyId] = Bounty({
            creator: msg.sender,
            targetId: _targetId,
            amount: msg.value,
            isActive: true
        });

        emit BountyCreated(bountyId, msg.sender, _targetId, msg.value);
        return bountyId;
    }

    function releaseBounty(uint256 _bountyId, address payable _introducer) external {
        Bounty storage bounty = bounties[_bountyId];
        require(bounty.isActive, "Bounty is not active");
        require(msg.sender == bounty.creator, "Only creator can release");

        bounty.isActive = false;
        
        (bool success, ) = _introducer.call{value: bounty.amount}("");
        require(success, "Transfer failed");

        emit BountyReleased(_bountyId, _introducer, bounty.amount);
    }

    function cancelBounty(uint256 _bountyId) external {
        Bounty storage bounty = bounties[_bountyId];
        require(bounty.isActive, "Bounty is not active");
        require(msg.sender == bounty.creator, "Only creator can cancel");

        bounty.isActive = false;
        
        (bool success, ) = msg.sender.call{value: bounty.amount}("");
        require(success, "Transfer failed");

        emit BountyCancelled(_bountyId, msg.sender, bounty.amount);
    }
}
