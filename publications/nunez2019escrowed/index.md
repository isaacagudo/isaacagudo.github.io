# Escrowed decryption protocols for lawful interception of encrypted data

- Authors: David Núñez, Isaac Agudo, Javier López
- Type: Journal article
- Language: English
- Venue: Journal article in *IET Information Security*, 13(5), 498–507.
- Year: 2019
- DOI: [10.1049/iet-ifs.2018.5082](https://doi.org/10.1049/iet-ifs.2018.5082)
- Page: https://isaacagudo.github.io/publications/nunez2019escrowed/

Abstract: Escrowed decryption schemes (EDSs) are public‐key encryption schemes with an escrowed decryption functionality that allows authorities to decrypt encrypted messages under investigation, following a protocol that involves a set of trusted entities called ‘custodians’; only if custodians collaborate, the requesting authority is capable of decrypting encrypted data. This type of cryptosystem represents an interesting trade‐off to privacy versus surveillance dichotomy. In this study, the authors propose two EDSs where they use proxy re‐encryption to build the escrowed decryption capability, so that custodians re‐encrypt ciphertexts, in a distributed way, upon request from an escrow authority, and the re‐encrypted ciphertexts can be opened only by the escrow authority. Their first scheme, called EDS, follows an all‐or‐nothing approach, which means that escrow decryption only works when all custodians collaborate. Their second scheme, called threshold EDS, supports a threshold number of custodians for the escrow decryption operation. They propose definitions of semantic security with respect to the authorities, custodians and external entities, and prove the security of their schemes, under standard pairing‐based hardness assumptions. Finally, they present a theoretical and experimental analysis of the performance of both schemes, which show that they are applicable to real‐world scenarios.
