from typing import List, Generator, Union
import requests, time, datetime
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import base64
import json

from requests.api import request

from .arguments import get_items_ids
from .errors import *
from .WalmartResponse import *

import logging

log = logging.getLogger(__name__)
log.setLevel('DEBUG')


# Affiliates API only
class WalmartIO:
    """
    The main Walmart IO API interface.
    Example call: 
    ```py
    wiopy = WalmartIO(private_key_version='1', private_key_filename='./WM_IO_private_key.pem', consumer_id='XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX')
    ```

    Optional:
    -------
    You can provide `daily_calls` if it is not the default 5000.  
    publisherId can also be provided and it will auto populate every querry. 
    If you give publisherId as a kwarg, it will overide the default one the class has
    """

    ENDPOINT = "https://developer.api.walmart.com/api-proxy/service"

    def __init__(
        self, *, 
        private_key_version:str='1', private_key_filename:str, consumer_id:str, 
        daily_calls:int=5000, publisherId:str=None
        ) -> None:
        """
        WalmartIO API Connection
        ------

        Params: 
        ------- 
         * private_key_version (str, optional) : The version of the private key
         * consumer_id (str) : The UUID generated for the client application
         * private_key_filename : The file with the private key. 
         To Generate the public and private key (https://walmart.io/key-tutorial). 
         The filename will look something like `./WM_IO_private_key.pem`
        
        Optional:
        -------
         * daily_calls (int) : Walmart grants 5000 daily calls to their API but you can ask for more.
         It can be assumed that this object will exist over multiple days, so total calls made in a day will be limited.
         https://walmart.io/termsandcondition
         * publisherId (str) : Your Impact Radius Publisher Id. 
         If provided, it will auto populate every querry with your id
        """


        self._private_key_version = private_key_version
        
        # IOError is triggered if the file cannot be opened
        with open(private_key_filename, 'r') as f:
            self._private_key = RSA.importKey(f.read())
        
        self._consumer_id = consumer_id
        
        self.headers = {}
        self.headers["WM_CONSUMER.ID"] = consumer_id
        self.headers["WM_SEC.KEY_VERSION"] = private_key_version

        self._update_daily_calls_time = datetime.datetime.now() + datetime.timedelta(days=1)
        self.daily_calls = daily_calls
        self.daily_calls_remaining = daily_calls

        self.publisherId = publisherId or None

        log.info(f"Walmart IO connection with consumer id ending in {consumer_id[-6:]}")

    def catalog_product(self, **kwargs) -> WalmartCatalog:
        """
        Catalog Product API allows a developer to retrieve the products catalog in a paginated fashion. 
        Catalog can be filtered by category, brand and/or any special offers like rollback, clearance etc.

        Params:
        -------
        * Named params passed in by kwargs (optional)

            publisherId:    Your Impact Radius id. If passed, this value will be set in the affiliate links in the response
            adId:       	Your Impact Radius Advertisement Id
            campaignId: 	Your Impact Radius Campaign Id
            category:   	Category id of the desired category. This should match the id field from Taxonomy API
            brand:      	Brand name
            specialOffer:	Special offers like rollback, clearance, specialBuy
            soldByWmt:     	Set it to true if you only want items sold by Walmart.com (excluding marketplace items)
            available:  	Set it to true if you only want items that are available to purchase (excluding out of stock items)
            count:      	Number of items the API will return


        `NOTE - It is recommend passing category or brand as query parameters for faster response times`
        """
        if 'nextPage' in kwargs:
            url = 'https://developer.api.walmart' + kwargs.pop('nextPage')
        else:
            url = self.ENDPOINT + '/affil/product/v2/paginated/items'

        response = self._send_request(url, **kwargs)
        return WalmartCatalog(response)

    def post_browsed_products(self, itemId:str) -> List[WalmartProduct]:
        """
        The post browsed products API allows you to recommend products to someone based on their product viewing history. 
        Similar to the Product Recommendation API, this endpoint uses one item ID as the anchor for the output. 
        For instance, if you know that one of your customers has recently viewed an Xbox one, it is likely that they may be also interested in purchasing a PlayStation 4, or Nintento Wii. 
        Some example use cases for this data:

         * Retargeting to your customers based on knowing their recent viewing history.
         * Understanding what other similar items a customer might purchase if the initial item they were interested in has gone out of stock.

        Params:
        -------
         * itemId (str) : Each item on Walmart.com has a particular item ID associated with it. 
        This can be generally seen in the last 8 digits of a URL string, but can also be acquired by using the Product Lookup API.

        Returns:
        -------
         * List[WalmartProduct] : The endpoint returns a maximum of 10 `WalmartProduct`s, being ordered from most relevant to least relevant for the customer.
        """
        url = f'{self.ENDPOINT}/affil/product/v2/postbrowse?itemId={itemId}'
        response = self._send_request(url)
        return [WalmartProduct(item) for item in response]

    def product_lookup(self, ids:Union[str, List[str]], **kwargs) -> List[WalmartProduct]:
        """
        Walmart product lookup

        For more info: (https://walmart.io/docs/affiliate/product-lookup)

        Params:
        -------
         * ids : list of ids to lookup
         * Named params passed in by kwargs (optional)
             
             publisherId:	Your Impact Radius Publisher Id
             adId:	        Your Impact Radius Advertisement Id
             campaignId:	Your Impact Radius Campaign Id
             format:    	Type of response required, allowed values [json, xml(deprecated)]. Default is json. 
             upc:       	upc of the item

        Returns:
        -------
         * products (List[WalmartProduct]) : List of products as objects
            List[ https://walmart.io/docs/affiliate/item_response_groups ]
        """
        url = self.ENDPOINT + '/affil/product/v2/items'

        params = kwargs
        ids = get_items_ids(ids)
        if len(ids) > 200:
            log.warning("For large id lists, try using bulk_product_lookup. It will continue to run even if one chunk of ids raise an error")
        products = []

        for idGroup in self._get_product_id_chunk(list(set(ids)), 20):
            params['ids'] = idGroup
            response = self._send_request(url, **params)
            for item in response['items']:
                products.append(WalmartProduct(item))
        
        return products

    def bulk_product_lookup(self, ids:Union[str, List[str]], amount:int=20, **kwargs):
        """
        Walmart product lookup for a bulk of products. It will keep going even if there are errors
        This function is a generator that gives you #amount products at a time

        For more info: (https://walmart.io/docs/affiliate/product-lookup)

        Params:
        -------
         * ids : list of ids to lookup
         * amount : the amount of products to yield at a time (max 20)
         * Named params passed in by kwargs (optional)
             
             publisherId:	Your Impact Radius Publisher Id
             adId:	        Your Impact Radius Advertisement Id
             campaignId:	Your Impact Radius Campaign Id
             format:    	Type of response required, allowed values [json, xml(deprecated)]. Default is json. 
             upc:       	upc of the item

        Yield:
        -------
         * List[WalmartProduct] : List of products as objects
            List[ https://walmart.io/docs/affiliate/item_response_groups ]
        """
        url = self.ENDPOINT + '/affil/product/v2/items'

        params = kwargs
        ids = get_items_ids(ids)

        # Keep amount [1, 20]
        amount = min(max(1, amount), 20)

        for idGroup in self._get_product_id_chunk(list(set(ids)), amount):
            params['ids'] = idGroup
            try:
                response = self._send_request(url, **params)
                yield [WalmartProduct(item) for item in response['items']]
            except InvalidRequestException as e:
                log.debug(f"bulk_product_lookup failed during the request with {idGroup} ids")
                log.debug(e)

    def product_recommendation(self, itemId:str) -> List[WalmartProduct]:
        """
        The Product recommendation API is an extension driven by the science that powers the recommended products container on Walmart.com. 
        Walmart has parsed 100s of millions of transactions over their product catalog of more than 6 million products to be able to deliver, with accuracy, the items in this response. 
        Some example use cases where a partner might be interested in utilizing this data:

         * A recommended products advertising widget via e-mail delivered right after a transaction has been verified
         * Retargeting on an ecommerce storefront anchored on a shared UPC between multiple merchants
         * An upsell to an existing customer presenting an array of products due to knowing their order history
        
        Params:
        -------
         * itemId (str) : Each item on Walmart.com has a particular item ID associated with it. 
        This can be generally seen in the last 8 digits of a URL string, but can also be acquired by using the Product Lookup API.

        Returns:
        -------
         * List[WalmartProduct] : The endpoint returns a maximum of 10 `WalmartProduct`s, being ordered from most relevant to least relevant for the customer.
        """
        url = url = f'{self.ENDPOINT}/affil/product/v2/nbp?itemId={itemId}'
        response = self._send_request(url)
        return [WalmartProduct(item) for item in response] 

    def reviews(self, itemId:str, **kwargs) -> WalmartReviewResponse:
        """
        The Reviews API gives you access to the extensive item reviews on Walmart that have been written by the users of Walmart.com. 
        This is great content for enriching item descriptions. 
        You are free to showcase this content on your application provided you link back to the original content page on Walmart.com, 
        as specified in the response parameter "productTrackingUrl".
        (https://walmart.io/docs/affiliate/reviews)

        Params:
        -------
         * itemId : the id of the item to query for its reviews
         * Query Parameters (optional) :
             
             publisherId:	Impact Radius Publisher Id  
             nextPage:	    Next Page of customer reviews. The value is available in previous response to the api call.


        Returns:
        -------
         * review (`WalmartReview`) : Walmart review object
        """
        if 'nextPage' in kwargs:
            page = kwargs.pop('nextPage').split('page=')[1]
            kwargs['page'] = page
            
        
        url = self.ENDPOINT + f'/affil/product/v2/reviews/{itemId}'
        response = self._send_request(url, **kwargs)
        return WalmartReviewResponse(response)

    def search(self, query:str, **kwargs) -> WalmartSearch:
        """
        Search API allows text search on the Walmart.com catalogue and returns matching items available for sale online.

        Item results returned by the API are paginated, with upto 25 items displayed per page (using the numItems parameter). 
        It is possible to request more by using the "start" parameter that specifies the first item number in the response. 
        Pagination is limited to the top 1000 items for a particular search. 

        Items are sorted by a user-specified order. 
        The default sort is by relevance. 
        Please see below for a list of available sort types.
        
        (https://walmart.io/docs/affiliate/search)

        Params:
        -------
         * query (str) : Search text - whitespace separated sequence of keywords to search for
         * Query Parameters (optional) :
             
             publisherId:	Your Impact Radius Publisher Id
             categoryId:	Category id of the category for search within a category. This should match the id field from Taxonomy API
             start:     	Starting point of the results within the matching set of items - upto 10 items will be returned starting from this item
             sort:      	Sorting criteria, allowed sort types are [relevance, price, title, bestseller, customerRating, new]. Default sort is by relevance.
             order:     	Sort ordering criteria, allowed values are [ascending, descending]. This parameter is needed only for the sort types [price].
             numItems:  	Number of matching items to be returned, max value 25. Default is 10.
             responseGroup:	Specifies the item fields returned in the response, allowed response groups are [base, full]. Default value is base. Refer Item Response Groups for details of exact fields returned by each response group.
             facet:	        Flag to enable facets. Default value is off. Set this to on to enable facets.
             facet.filter:	Filter on the facet attribute values. This parameter can be set to <facet-name>:<facet-value> (without the angles). Here facet-name and facet-value can be any valid facet picked from the search API response when facets are on.
             facet.range:	Range filter for facets which take range values, like price. See usage above in the examples.
        
        Returns:
        ------
         * WalmartSearch: Walmart Search object
        """
        if "facet" in kwargs:
            facet = kwargs["facet"]
            if type(facet) == bool:
                kwargs["facet"] = "on" if facet else "off"

        if "range" in kwargs:
            kwargs["facet.range"] = kwargs.pop("range")
            kwargs["facet"] = "on"
        if "filter" in kwargs:
            kwargs["facet.filter"] = kwargs.pop("filter")
            kwargs["facet"] = "on"

        kwargs['query'] = query
        

        url = self.ENDPOINT + '/affil/product/v2/search'
        response = self._send_request(url, **kwargs)
        return WalmartSearch(response)

    def stores(self, **kwargs) -> List[WalmartStore]:
        """
        Store Locator API helps locate nearest Walmart Stores via API. 
        It lets users search for stores by latitude and longitude, and by zip code.

        Params (optional):
        -------
         * lat : Latitude
         * lon : Longitude
         * zip : Zip

        Returns:
        -------
         * store ('WalmartStore') : closest store to specified location
        """
        if not (('lat' in kwargs and 'lon' in kwargs) or ('zip' in kwargs)):
            raise InvalidParameterException("Missing lat & lon OR zip parameter")

        url = self.ENDPOINT + '/affil/product/v2/stores'
        response = self._send_request(url, **kwargs)
        return [WalmartStore(store) for store in response]

    def taxonomy(self, **kwargs) -> WalmartTaxonomy:
        """
        The taxonomy service exposes the taxonomy used to categorize items on Walmart.com.

        The Taxonomy API exposes the category taxonomy used by Walmart.com to categorize items. 
        It describes three levels: Departments, Categories and Sub-categories as available on Walmart.com. 
        It is possible to specify the exact category as a parameter when using any of the API's below:
        * Search
        * Catalog Product

        For example, Search API can be restricted to search within a category by supplying id as per the taxonomy.
        
        Params:
        ------
         * Query (optional):
            unknown; WalmartIO documentation does not expose what the acceptable 
        """
        url = self.ENDPOINT + '/affil/product/v2/taxonomy'
        return self._send_request(url, **kwargs)
        
    def trending(self, publisherId=None) -> List[WalmartProduct]:
        """
        The Trending Items API is designed to give the information on what is bestselling on Walmart.com right now. 
        The items returned by this service are a curated list based on the collective browsing and sales activity of all of Walmart's users. 
        The data for this services is updated multiple times a day. 
        You can expect a high clickthrough and conversion rate on these items if you choose to advertise them.

        Params:
        -------
         * Query (optional) :
            publisherId:    Your Impact Radius Publisher Id
        
        Returns:
        -------
         * products (`List[WalmartProduct]`) : a list of walmart products on the trending list
        """
        
        url = self.ENDPOINT + '/affil/product/v2/trends'
        
        if publisherId:
            response = self._send_request(url, publisherId=publisherId)
        else:
            response = self._send_request(url)
        return [WalmartProduct(item) for item in response['items']]

    def _get_headers(self) -> dict:
        """
        To make a call to the API, headers are needed. This function will return those headers for a call.
        (https://walmart.io/docs/affiliate/onboarding-guide)

        Returns
        -------
         * headers (dict) : {
             'WM_CONSUMER.ID' : consumerId,  
             'WM_CONSUMER.INTIMESTAMP' : epoxTime,  
             'WM_SEC.AUTH_SIGNATURE' : signature_enc,  
             'WM_SEC.KEY_VERSION' : keyVersion
         }  
        """
        
        timeInt = int(time.time()*1000)

        self.headers["WM_CONSUMER.INTIMESTAMP"] = str(timeInt)

        # <--- WM_SEC.AUTH_SIGNATURE --->
        # The signature generated using the private key and signing the values of consumer id, timestamp and key version. 
        # The TTL of this signature is 180 seconds. Post that, the API Proxy will throw a "timestamp expired" error.
        
        sortedHashString = self.headers['WM_CONSUMER.ID'] +'\n' \
                            + self.headers['WM_CONSUMER.INTIMESTAMP'] +'\n' \
                            + self.headers['WM_SEC.KEY_VERSION']+'\n'
        encodedHashString = sortedHashString.encode()

        hasher = SHA256.new(encodedHashString)
        signer = PKCS1_v1_5.new(self._private_key)
        signature = signer.sign(hasher)
        signature_enc = str(base64.b64encode(signature),'utf-8')

        self.headers['WM_SEC.AUTH_SIGNATURE'] = signature_enc

        return self.headers

    def _send_request(self, url, **kwargs) -> dict:
        """
        Sends a request to the Walmart API and return the HTTP response.
        -------
        
        Format is json by default and cannot be changed through kwargs. xml is deprecated.  
        Send richAttributes='true' by default. Can be set to 'false' through kwargs
        
        Params:
        -------
         * url (str): The endpoint url to make the request
         * Named params passed in kwargs can be any of the optional GET arguments specified in the Walmart specification
        
        Returnes:
        -------
         * response : HTTP response from url
         
        Errors:
        -------
         * (`InvalidRequestException`) : 
            If the response's status code is differente than 200 or 201, raise an InvalidRequestException with the appripiate code
         * (`DailyCallLimit`) : 
            If the object has ran out of API calls for the day, the error is raised
        """
        log.debug(f"Making connection to {url}")

        # Avoid format to be changed, always go for json
        kwargs.pop('format', None)
        request_params = {}
        for key, value in kwargs.items():
            request_params[key] = value

        # Convert from native boolean python type to string 'true' or 'false'. This allows to set richAttributes with python boolean types
        if 'richAttributes' in request_params and type(request_params['richAttributes'])==bool:
            if request_params['richAttributes']:
                request_params['richAttributes']='true'
            else:
                request_params['richAttributes']='false'
        else:
            # Even if not specified in arguments, send request with richAttributes='true' by default
            request_params['richAttributes']='true'

        if self.publisherId and 'publisherId' not in request_params:
            request_params['publisherId'] = self.publisherId

        
        if not self._validate_call():
            raise DailyCallLimit("Too many calls in one day. If this is incorrect, try increasing `daily_calls`")

        if request_params:
            response = requests.get(url, headers=self._get_headers(), params=request_params)
        else:
            response = requests.get(url, headers=self._get_headers())
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        else:
            if response.status_code == 400:
                # Send exception detail when it is a 400 bad error
                raise InvalidRequestException(response.status_code, detail=response.json()['errors'][0]['message'])
            else:
                raise InvalidRequestException(response.status_code)

    def _validate_call(self) -> bool:
        """
        Check if the caller has API calls remaining
        If there are remaining calls, check to see if the headers need to be updated. If so, update them.
        
        Returns:
        -------
         * (bool) : if there are still remaining calls for the day

        Errors:
        -------
         * `DailyCallLimit` : raises an error if there are no remaining calls 
        """
        if datetime.datetime.now() > self._update_daily_calls_time:
            self.daily_calls_remaining = self.daily_calls
            self._update_daily_calls_time = datetime.datetime.now() + datetime.timedelta(days=1)

        if self.daily_calls_remaining > 0:
            self.daily_calls_remaining -= 1
            if self.daily_calls_remaining == 500:
                log.warning("500 calls remain for the day")
            return True
        
        return False

    @staticmethod
    def _get_product_id_chunk(full_list: List[str], chunk_size:int) -> Generator[str, None, None]:
        """Yield successive chunks from List."""
        for i in range(0, len(full_list), chunk_size):
            yield ','.join(full_list[i:i + chunk_size])


