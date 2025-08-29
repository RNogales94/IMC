# IMC Python Exercise

In this exercise your task is to modify a simple API client that interacts with a public API which has info about SpaceX
events. The documentation for this API can be found [here](https://github.com/r-spacex/SpaceX-API/blob/master/docs/README.md) ,
or you can see them in Postman [here](https://docs.spacexdata.com/).

## General Instructions

This exercise contains two tasks. For both of these tasks, you will need to modify the code provided in the
file `client.py`. You are not required to create any other files, but you may if you wish to do so.

Your Python environment should have version 3.9 or later and should have the `requests`
library installed.

If you need to make any assumptions during the completion of the tasks, please note the assumption(s) down in a comment
or docstring next to the relevant section of code.

You may modify the provided code in any way you deem necessary to best complete the given tasks.

## Task 1: Modify `get_launches()`

Currently, the `get_launches()` method returns a list of all launches since the beginning of SpaceX. Your task is to
modify the method to accept a start date and an end date, and to only return launches that have occurred or will occur
between those dates. You can find the docs for the `launches/query` endpoint via the documentation links above.

Requirements for the altered implementation of `get_launches()`:

- it must accept two optional parameters: `start_date` and `end_date`, both of type
  `datetime.date`
- if both parameters are supplied, it must only return launches occurring in the interval `[start_date, end_date]` (this
  is inclusive of both start and end)
- if `start_date` is not supplied or `None`, it must return launches since the very beginning
- if `end_date` is not supplied or `None`, it must return launches until the most recent
- there is no need to account for the `date_precision`, `tbd` flag, nor the `net` flag of the launch
  ([described here](https://github.com/r-spacex/SpaceX-API/blob/master/docs/README.md#launch-date-field-explanations))
- it must return a list of `Launch` objects (which may be empty if there are no launches in the given range)

## Task 2: Implement `get_heaviest_launch()`

The method `get_heaviest_launch()` is currently not implemented. Your task is to implement it so that it returns
a `Launch` object representing the launch that has the heaviest
**total** payload (launches may have multiple payloads so they must be added together). Note that the `/launches`
endpoint only returns a list of payload ids by default, so you will need to find out how to get the payload mass by
reading the API documentation.

Requirements for the implementation of `get_heaviest_launch()`:

- the `start_date` and `end_date` parameters must follow the same rules specified in
  `get_launches()`
- it must return a `Launch` object which has the heaviest total payload in the date range, stored in the attribute `total_payload_mass_kg`
- `None` must be returned if there are no launches in the date range

