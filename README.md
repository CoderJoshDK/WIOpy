# WallmartIO Python Wrapper - WIOpy

A python wrapper for the wallmart io API. Only supports the Affiliate API for now. If you would like to help contribute; contact me at : ___

## How to use  
An example of creating a WIOpy connection 
```py
from walmart-io-wrapper import WalmartIO

wiopy = WalmartIO(private_key_version='1', private_key_filename='./WM_IO_private_key.pem', consumer_id='XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX')
```

## Response Examples
When making a call to the API, an object will be returned. That object is an object version of returned json.  
There are two ways to get info from the object:
 - ```data.name```
 - ```data['name']```  
Some attributes will return a dict and not an object due to a lack of documentation from Walmart.  
When getting an attribute from a `WalmartResponse`, it will return either `response` or `None`. But trying to get an attribute of `None` will still raise an error.

## Examples of calls
### Product lookup
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
Remember: product_lookup always returns a list of WalmartProducts

### Stores
The API can return a list of closest stores near a specified location. Either zip code or lon/lat  
```py
data = wiopy.stores(lat=29.735577, lon=-95.511747)
```
