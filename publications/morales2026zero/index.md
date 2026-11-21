# Zero-knowledge Bitcoin mixer with reversible unlinkability

- Authors: Daniel Morales, Isaac Agudo, Javier López
- Type: Journal article
- Language: English
- Venue: Journal article in *Blockchain: Research and Applications*, 7(2), 100323.
- Year: 2026
- DOI: [10.1016/j.bcra.2025.100323](https://doi.org/10.1016/j.bcra.2025.100323)
- Open-access copy: https://doi.org/10.1016/j.bcra.2025.100323
- Page: https://isaacagudo.github.io/publications/morales2026zero/

Abstract: Cryptocurrencies, particularly Bitcoin, continue to be the most prevalent use case within the blockchain ecosystem. One of the inherent limitations of blockchain is that it can create a false sense of privacy. All transaction history and the amount of cryptocurrency held are publicly available, and this information can be easily associated with specific individuals. Many works have proposed fully-private solutions, which are ideal but not realistic in many scenarios. This paper proposes a technical solution that enables private Bitcoin payments by default, but with the option to conditionally disclose payment data. To do so, this solution relies on unlinkability by a decentralized mixer, which can be reversed by a conditional discloser using a trapdoor unlinkability function. The conditional discloser, which also provides accountability of requests, obeys the payer's policies regarding who can access payment data. To ensure compliance, we propose a mixer that does not learn anything about the payment link, but is guaranteed by Zero-Knowledge Proofs that the payment can be relinked by a specific conditional discloser. Furthermore, we provide a proof-of-concept implementation of the proofs, using Circom and SnarkJS. We also present a benchmark that demonstrates the feasibility of this solution. It incurs only one additional parameter per on-chain transaction, while the remainder of the verification data is managed off-chain.
