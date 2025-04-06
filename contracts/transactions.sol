// SPDX-License-Identifier: MIT 
// contracts/FraudLogger.sol
pragma solidity ^0.8.0;

contract FraudLogger {
    event LogStored(string transactionHash, uint256 amount, string method, string result);

    struct Log {
        string transactionHash;
        uint256 amount;
        string method;
        string result;
    }

    Log[] public logs;

    function storeLog(string memory transactionHash, uint256 amount, string memory method, string memory result) public {
        logs.push(Log(transactionHash, amount, method, result));
        emit LogStored(transactionHash, amount, method, result);
    }

    function getLog(uint index) public view returns (string memory, uint256, string memory, string memory) {
        require(index < logs.length, "Index out of bounds");
        Log memory log = logs[index];
        return (log.transactionHash, log.amount, log.method, log.result);
    }

    function getTotalLogs() public view returns (uint) {
        return logs.length;
    }
}
