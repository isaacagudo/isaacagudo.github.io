# Integration of MPC into Besu through an extended private transaction model

- Authors: Daniel Morales, Isaac Agudo, Javier López
- Type: Conference paper
- Venue: Conference paper in *2023 IEEE International Conference on Metaverse Computing, Networking and Applications (MetaCom)*, pp. 266–273.
- Year: 2023
- DOI: [10.1109/metacom57706.2023.00056](https://doi.org/10.1109/metacom57706.2023.00056)
- Page: https://isaacagudo.github.io/publications/morales2023integration/

Abstract: In the last few years we have seen many different approaches to incorporate privacy features to blockchains. In the area of cryptocurrencies that would normally mean protecting the identity of the owner of some funds, but there are other applications where privacy is even more important, especially in permissioned blockchains. Permissioned blockchain platforms, such as Hyperledger Besu or Hyperledger Fabric, already include the concept of private transactions, which essentially defines a sub-group of the blockchain where their participants share some private data. We want to go one step ahead and propose an extended model for private transactions where the different participants can have a separated view of the same transaction, allowing the integration of Multi-party Computation protocols in the blockchain. Our work extends Hyperledger Besu’s design for private transactions, offering better security properties and a finer grain customization. We cover two specific MPC examples, Private Set Intersection and Byzantine Fault-Tolerant Random Number Generation, and propose a mechanism to run them using smart contract interfaces.
