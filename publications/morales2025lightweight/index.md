# A Lightweight Mechanism for Dynamic Secret Sharing of Private Data by Constrained Devices

- Authors: Daniel Morales, Isaac Agudo, Javier López
- Type: Journal article
- Language: English
- Venue: Journal article in *IEEE Internet of Things Journal*, 12(13), 22725–22732.
- Year: 2025
- DOI: [10.1109/jiot.2025.3555026](https://doi.org/10.1109/jiot.2025.3555026)
- Open-access copy: https://doi.org/10.1109/jiot.2025.3555026
- Page: https://isaacagudo.github.io/publications/morales2025lightweight/

Abstract: Outsourced computations are essential for IoT devices, but they can raise privacy issues. Privacy-preserving technologies, such as Secure Multiparty Computation, can be used to delegate computations on private data from multiple devices while disclosing nothing but the output, but they may come at a prohibitive cost. In particular, Secret Sharing-based Secure Multiparty Computation requires the device to establish n independent confidential channels for each shared message, one channel per holder. This work proposes a new approach for IoT devices to secretly share private data with a committee of holders by broadcasting a single ciphertext. A straightforward solution is Homomorphic Encryption with Decryption to Shares from Chillotti et al., 2022, but it requires Fully Homomorphic Encryption and is not dynamic. Additionally, we propose Oblivious Sharing Re-Encryption, which is a new family of protocols that achieve this lightweight private data sharing without requiring Fully Homomorphic Encryption, and which is also more dynamic. We provide a concrete implementation based on NTRU encryption, together with a security proof and performance analysis. The analysis shows that OSRE outperforms the standard setting with n confidential channels when the device sends more than one message.
