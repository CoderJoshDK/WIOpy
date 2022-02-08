[![Python](https://img.shields.io/badge/Python->3.6-%23FFD140)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/WIOpy)](https://pypi.org/project/WIOpy/)
[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/CoderJoshDK/WIOpy?include_prereleases)](https://github.com/CoderJoshDK/WIOpy)
[![GitHub issues](https://img.shields.io/github/issues/CoderJoshDK/WIOpy)](https://github.com/CoderJoshDK/WIOpy/issues)
[![GitHub Repo stars](https://img.shields.io/github/stars/CoderJoshDK/WIOpy?style=social)](https://github.com/CoderJoshDK/WIOpy)

# WalmartIO Python Wrapper - WIOpy

A python wrapper for the Walmart io API. Only supports the Affiliate API for now. The project is open to contributions 

## Getting it

To download WIOpy, either fork this github repo or simply use Pypi via pip.
```sh
$ pip install WIOpy
```  
To upgrade the package simply run  
```sh
$ pip install WIOpy --upgrade
```  

## How to use  
An example of creating a WIOpy connection   
One important note is that you need to pass in the private key file location.  
```py
from WIOpy import WalmartIO

wiopy = WalmartIO(private_key_version='1', private_key_filename='./WM_IO_private_key.pem', consumer_id='XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX')
data = wiopy.product_lookup('33093101')[0]
```
WIOpy also supports asynchronous calls. To use, everything will be the same but you must await a call and the contructed object is different.
```py
from WIOpy import AsyncWalmartIO
wiopy = AsyncWalmartIO(...)
data = await wiopy.product_lookup('33093101')[0]
```

## Response Examples
When making a call to the API, an object will be returned. That object is an object version of returned JSON.  
There are two ways to get info from the object:
 - `data.name`  
 - `data['name']`  
An example of a returned object and one that is not (review/search are variables returned):
 - `review.reviewStatistics.averageOverallRating` # Nested call
 - `search.facets` # Gives back a dict that can now be used like a dict and not object  
Some attributes will return a dict and not an object due to a lack of documentation from Walmart.  
When getting an attribute from a `WalmartResponse`, it will return either `response` or `None`\. But trying to get an attribute of `None` will still raise an error.
[Extra details on calls and responses](walmart.io/docs). However, the docs are inconsistent and lack typical practices such as response schema. That is why something like the search facets response is missing because the docs show it is in the response but not what type of data it will contain.  
While there may be a response missing or a response not being converted to an object, please check [WalmartResponse](./wiopy/WalmartResponse.py) to get an idea of what a response will return. Some properties are not always present in a response.  


## Examples of calls

### [Catalog Product](https://walmart.io/docs/affiliate/paginated-items)
Catalog Product API allows a developer to retrieve the products catalog in a paginated fashion. Catalog can be filtered by category, brand and/or any special offers like rollback, clearance etc.
```py
data = wiopy.catalog_product(category='3944', maxId='8342714')
```
A catalog response contains category, format, nextPage, totalPages, and a list of items


### [Post Browsed Products](https://walmart.io/docs/affiliate/post-browsed-products)
The post browsed products API allows you to recommend products to someone based on their product viewing history.
```py
data = wiopy.post_browsed_products('54518466')
```
Response gives top 10 relevent items to the given id


### [Product lookup](https://walmart.io/docs/affiliate/product-lookup)
There are two ways to lookup a product   
The first is to pass a single string in
```py
data = wiopy.product_lookup('33093101')[0]
```
or you can pass a list of strings
```py
data = wiopy.product_lookup('33093101, 54518466, 516833054')
data = wiopy.product_lookup(['33093101', '54518466', '516833054'])
```
Remember: product_lookup always returns a list of [WalmartProducts](https://walmart.io/docs/affiliate/item_response_groups)  


### [Bulk product lookup](https://walmart.io/docs/affiliate/product-lookup)
`bulk_product_lookup` is similar to `product_lookup` however, the bulk version does not raise errors and it is a generator.  
Items are passed in as chunks of max size 20. If an error occurs on that call, all items will be lost. But the entire call will not be lost.  
```py
data = wiopy.bulk_product_lookup('33093101, 54518466, 516833054', amount=1)
for items in data:
    for item in items:
        print(item)
```
Response gives generator of [WalmartProducts](https://walmart.io/docs/affiliate/item_response_groups)  
If you are unfamiliar with async generators; to properly call the async version:
```py
data = wiopy.bulk_product_lookup('33093101, 54518466, 516833054')
async for items in data:
```


### [Product Recommendation](https://walmart.io/docs/affiliate/product-recommendation)
Get recommendations based on a given product id
```py
data = wiopy.product_recommendation('54518466')
```
Response gives a list of related products


### [Reviews](https://walmart.io/docs/affiliate/reviews)
The Reviews API gives you access to the extensive item reviews on Walmart that have been written by the users of Walmart.com
```py
data = wiopy.reviews('33093101')
```
Response gives review data


### [Search](https://walmart.io/docs/affiliate/search)
Search API allows text search on the Walmart.com catalogue and returns matching items available for sale online.
```py
# Search for tv within electronics and sort by increasing price:
data = wiopy.search('tv', categoryId='3944', sort='price', order='ascending')
```
You can also add facets to your search
```py
data = wiopy.search('tv', filter='brand:Samsung')
```
The search response gives back a list of products and some meta data. It returns a `facets` element but there is no detail on the API about what it could return. It is a list of some unknown type


### [Stores](https://walmart.io/docs/affiliate/stores)
The API can return a list of closest stores near a specified location. Either zip code or lon/lat  
```py
data = wiopy.stores(lat=29.735577, lon=-95.511747)
```


### [Taxonomy](https://walmart.io/docs/affiliate/taxonomy)
The taxonomy service exposes the taxonomy used to categorize items on Walmart.com.  
Details about params is missing from docs
```py
data = wiopy.taxonomy()
```


### [Trending Items](https://walmart.io/docs/affiliate/trending-items)
The Trending Items API is designed to give the information on what is bestselling on Walmart.com right now.
```py
data = wiopy.trending()
```

## Logging
WIOpy supports logging via the logging module. Configuration of the logging module can be as simple as:
```py
import logging

logging.basicCongif(level=logging.INFO)
```

-------
![License](https://img.shields.io/github/license/CoderJoshDK/WIOpy)
![GitHub last commit](https://img.shields.io/github/last-commit/CoderJoshDK/WIOpy)
