# DLPNO-CCSD(T) Package

This directory contains the initial scaffolding for DLPNO-CCSD(T) (Domain-based Local Pair Natural Orbital Coupled Cluster with Singles, Doubles, and Perturbative Triples) implementation in Tangelo.

## Overview

DLPNO-CCSD(T) is a linear-scaling coupled cluster method that reduces computational cost by exploiting the local nature of electron correlation.

## Package Structure

- `config.py`: Configuration parameters and validation
- `structures.py`: Data structures for DLPNO calculations
- `convergence.py`: Convergence monitoring utilities
- `logging_utils.py`: Logging infrastructure
- `paths.py`: Utility functions for path and key generation
- `localization/`: Localization methods and adapters

## Status

This is an initial scaffolding implementation. Algorithmic logic and computational kernels are not yet implemented.
