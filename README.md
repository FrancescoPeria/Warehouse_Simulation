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
The inventory built for a specific product is influenced by:
- The time interval (replenishment period R) until next production
- The estimated demand in that time interval

Main assumptions:
- I assumed the replenishment period R to be deterministic
- I assumed actual sales as a proxy of the demand. This means that everything is produced is exactly sold. This assumption allows me to understand the exact relation between the replenishment period R and the fill rate of the warehouse. In fact it's possible to introduce a "sales forecast" as a proxy of demand, but this implies that the inventory produced is also increased by the forecast error

The inventory is simulated code by code. Since no optimal sequence is first provided, a Monte Carlo Simulation has been used to put together the inventory of all the codes. In fact I forced every product to start the simulation at a random timestamp and then I summed up the inventory for all the codes day by day.
I performed this experiment multiple times obtaining different warehouse stock evolutions. By taking the average result it's possible to see how the production frequency and the demand for each code influences the total inventory built overtime
