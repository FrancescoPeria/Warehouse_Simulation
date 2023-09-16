# Warehouse_Simulation
I Created the class Product to simulate the fill rate of a warehouse overtime.
These are the attributes used to model the instance "product":
- code --> ID associated to a product
- name
- line --> manufacturing line associated to a product
- productivity --> production rate of a product on a machine
- cases_PAL --> how many cases in a pallet
- stacking --> how many pallets could be stacked to load a truck
- demand --> weekly time series used to model the demand. It could be "sales orders", "forecasts" or "actual sales"
- R --> replenishment period between two consecutive productions
- daily_sold --> time series used to model daily sales for a specific product

The scope of this project is to model the evolution of the warehouse overtime, as a consequence of the production of different codes.
