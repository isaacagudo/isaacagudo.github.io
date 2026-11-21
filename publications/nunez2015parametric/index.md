# A Parametric Family of Attack Models for Proxy Re-encryption

- Authors: David Núñez, Isaac Agudo, Javier López
- Type: Conference paper
- Language: English
- Venue: Conference paper in *2015 IEEE 28th Computer Security Foundations Symposium*, pp. 290–301.
- Year: 2015
- DOI: [10.1109/csf.2015.27](https://doi.org/10.1109/csf.2015.27)
- Open-access copy: https://ieeexplore.ieee.org/ielx7/7243288/7243713/07243740.pdf
- Page: https://isaacagudo.github.io/publications/nunez2015parametric/

Abstract: Proxy Re-Encryption (PRE) is a type of Public-Key Encryption (PKE) that provides an additional re-encryption functionality. Although PRE is inherently more complex than PKE, attack models for PRE have not been developed further than those inherited from PKE. In this paper we address this gap and define a parametric family of attack models for PRE, based on the availability of both the decryption and re-encryption oracles during the security game. This family enables the definition of a set of intermediate security notions for PRE that ranges from "plain" IND-CPA to "full" IND-CCA. We analyze some relations among these notions of security, and in particular, the separations that arise when the re-encryption oracle leaks re-encryption keys. In addition, we discuss which of these security notions represent meaningful adversarial models for PRE. Finally, we provide an example of a recent "CCA1-secure" scheme from PKC 2014 whose security model does not capture chosen-cipher text attacks through re-encryption and for which we describe an attack under a more realistic security notion. This attack emphasizes the fact that PRE schemes that leak re-encryption keys cannot achieve strong security notions.
