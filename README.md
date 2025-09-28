# Dataspace Demo for Collaborative Research

This repository provides supplementary material for the paper *Dataspaces for Collaborative Research*.  
It contains deployment instructions, use case material, and configuration examples that complement the work described in the publication.

---

## Repository Contents

- **`connector-setup/`**  
  Instructions for deploying and configuring dataspace connectors.  
  Includes a step-by-step guide (`connector_setup_instructions.pdf`) prepared during the IoP dataspace deployment.

- **`use-cases/`**  
  Supplementary material for the two pilot use cases explored in the paper:  
  - `dataset-finder-integration/`: Extension of the Dataset Finder with data exchange functionality.  
  - `federated-process-mining/`: Material from the federated process mining case study, including code and data as provided in the original repository.

- **`rest-endpoint-config/`**  
  Example code for configuring a REST endpoint to interact with the dataspace.

---

## Prerequisites

The material in this repository assumes that dataspace core components and connectors are deployed using the [German Culture Dataspace stack](https://github.com/Fraunhofer-FIT-DSAI/drkultur-edc).  
Please ensure this stack is available before attempting to use the provided instructions or code.

---

## How to Use

- Consult the **`connector-setup/`** folder if you wish to reproduce the connector deployment.
- Use the code in **`endpoint-config/`** as a reference for customizing dataspace endpoints.
- Explore the **`use-cases/`** folder for the supplementary material of the scenarios described in the paper.
  - **Dataset Finder Integration**  
  The Dataset Finder is available at [Dataset Finder repository](https://github.com/dsma-org/dataset-finder).  
  The integration connects the Dataset Finder with dataspace-based exchange mechanisms.
  To be able to reference a specific offer in the connector, we modified the [drkultur-edc-ui](https://github.com/Fraunhofer-FIT-DSAI/drkultur-edc-ui) to take a search string as a url parameter. This required modifying the following function to the [catalog-browser-page component](https://github.com/Fraunhofer-FIT-DSAI/drkultur-edc-ui) as follows:
```typescript
  ngOnInit(): void {
    this.activatedRoute.queryParams.subscribe(params => {
      const assetID = params['asset'];
      this.searchText.setValue(assetID)
    });
    ...
  }
```


  


  - **Federated Process Mining**  
  In **`federated-process-mining/`**, find the material to reproduce the federated process mining case study.  


This repository is intended as a reference for researchers and practitioners interested in deploying and experimenting with dataspaces in collaborative research contexts.

---

## License

This repository is licensed under the [Apache License 2.0](LICENSE).

---

## Citation

If you use material from this repository, please cite the accompanying paper:

> [Authors]. *Dataspaces for Collaborative Research*. [Conference/Journal], [Year].
