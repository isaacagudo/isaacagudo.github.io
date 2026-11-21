# Learning Multi-Party Adversarial Encryption and Its Application to Secret Sharing

- Authors: Ishak Meraouche, Sabyasachi Dutta, Sraban Kumar Mohanty, Isaac Agudo, Kouichi Sakurai
- Type: Journal article
- Venue: Journal article in *IEEE Access*, 10, 121329–121339.
- Year: 2022
- DOI: [10.1109/access.2022.3223430](https://doi.org/10.1109/access.2022.3223430)
- Open-access copy: https://ieeexplore.ieee.org/ielx7/6287639/6514899/09955544.pdf
- Page: https://isaacagudo.github.io/publications/meraouche2022learning/

Abstract: Neural networks based cryptography has seen a significant growth since the introduction of adversarial cryptography which makes use of Generative Adversarial Networks (GANs) to build neural networks that can learn encryption. The encryption has been proven weak at first but many follow up works have shown that the neural networks can be made to learn the One Time Pad (OTP) and produce perfectly secure ciphertexts. To the best of our knowledge, existing works only considered communications between two or three parties. In this paper, we show how multiple neural networks in an adversarial setup can remotely synchronize and establish a perfectly secure communication in the presence of different attackers eavesdropping their communication. As an application, we show how to build Secret Sharing Scheme based on this perfectly secure multi-party communication. The results show that it takes around 45,000 training steps for 4 neural networks to synchronize and reach equilibria. When reaching equilibria, all the neural networks are able to communicate between each other and the attackers are not able to break the ciphertexts exchanged between them.
