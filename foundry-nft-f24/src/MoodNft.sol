// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

import {ERC721}  from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Base64}  from "@openzeppelin/contracts/utils/Base64.sol";


contract MoodNft is ERC721, Ownable {
    error ERC721Metadata__URI_QueryFor_NonExistingToken();
    error MoodNft___CantFlipMoodIfNotOwner();

    event CreateNFT(uint256 indexed tokenId);

    enum NFTState {
        HAPPY,
        SAD
    }

    uint256 private s_tokenCounter;
    string private s_sadSvg;
    string private s_happySvg;

    mapping(uint256 => NFTState) private s_tokenIdToState;

    constructor(string memory sadSvg, string memory happySvg) ERC721("Mood NFT", "MN") Ownable(msg.sender) {
        s_tokenCounter = 0;
        s_sadSvg = sadSvg;
        s_happySvg = happySvg;
    }

    function mintNft() public {
        _safeMint(msg.sender, s_tokenCounter);
        // s_tokenIdToState[s_tokenCounter] = NFTState.SAD;
        emit CreateNFT(s_tokenCounter);
        s_tokenCounter++;
    }

    function flipMood(uint256 tokenId) public {
        if (getApproved(tokenId) != msg.sender && ownerOf(tokenId) != msg.sender) {
            revert MoodNft___CantFlipMoodIfNotOwner();
        }

        if (s_tokenIdToState[tokenId] == NFTState.HAPPY) {
            s_tokenIdToState[tokenId] = NFTState.SAD; 
        } else {
            s_tokenIdToState[tokenId] = NFTState.HAPPY;
        }
    }

    function _baseURI() internal pure override returns (string memory) {
        return "data:application/json;base64,";
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        if (ownerOf(tokenId) == address(0)) {
            revert ERC721Metadata__URI_QueryFor_NonExistingToken();
        }

        string memory imageURI = s_happySvg;

        if (s_tokenIdToState[tokenId] == NFTState.SAD) {
            imageURI = s_sadSvg;
        }

        string memory tokenMetadata = string(abi.encodePacked(_baseURI(), Base64.encode(bytes(abi.encodePacked(
            '{"name": "',
            name(),
            '", "description":"An NFT that reflects the mood of the owner, 100% on Chain!", ',
            '"attributes": [{"trait_type": "moodiness", "value": 100}], "image":"',
            imageURI,
            '"}'
        )))));

        return tokenMetadata;
    }

    function getHappySVG() public view returns (string memory) {
        return s_happySvg;
    }

    function getSadSVG() public view returns (string memory) {
        return s_sadSvg;
    }

    function getTokenCounter() public view returns (uint256) {
        return s_tokenCounter;
    }
}