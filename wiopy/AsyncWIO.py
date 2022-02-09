from operator import is_
from typing import List, Generator, Union
import requests, time, datetime
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import base64
import json

import aiohttp

from .arguments import *
from .errors import *
from .WalmartResponse import *
from .WalmartIO import WalmartIO

import logging

log = logging.getLogger(__name__)
log.setLevel('DEBUG')

class AsyncWalmartIO:
    """
    The main Walmart IO API interface as async calls.
    Example call: 
    ```py
    wiopy = AsyncWalmartIO(private_key_version='1', private_key_filename='./WM_IO_private_key.pem', consumer_id='XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX')
    ```

    Optional:
    -------
    You can provide `daily_calls` if it is not the default 5000.  
    publisherId can also be provided and it will auto populate every querry. 
    If you give publisherId as a kwarg, it will overide the default one the class has
    """

    ENDPOINT = "https://developer.api.walmart.com/api-proxy/service"

    @is_documented_by(WalmartIO.__init__)
    def __init__(
        self, *, 
        private_key_version:str='1', private_key_filename:str, consumer_id:str, 
        daily_calls:int=5000, publisherId:str=None
        ) -> None:
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

    @is_documented_by(WalmartIO.catalog_product)
    async def catalog_product(self, **kwargs) -> WalmartCatalog:
        if 'nextPage' in kwargs:
            url = 'https://developer.api.walmart' + kwargs.pop('nextPage')
        else:
            url = self.ENDPOINT + '/affil/product/v2/paginated/items'

        response = await self._send_request(url, **kwargs)
        return WalmartCatalog(response)

    @is_documented_by(WalmartIO.post_browsed_products)
    async def post_browsed_products(self, itemId:str) -> List[WalmartProduct]:
        url = f'{self.ENDPOINT}/affil/product/v2/postbrowse?itemId={itemId}'
        response = await self._send_request(url)
        return [WalmartProduct(item) for item in response]

    @is_documented_by(WalmartIO.product_lookup)
    async def product_lookup(self, ids:Union[str, List[str]], **kwargs) -> List[WalmartProduct]:
        url = self.ENDPOINT + '/affil/product/v2/items'

        params = kwargs
        ids = get_items_ids(ids)
        if len(ids) > 200:
            log.warning("For large id lists, try using bulk_product_lookup. It will continue to run even if one chunk of ids raise an error")
        products = []

        for idGroup in self._get_product_id_chunk(list(set(ids)), 20):
            params['ids'] = idGroup
            response = await self._send_request(url, **params)
            for item in response['items']:
                products.append(WalmartProduct(item))
        
        return products

    @is_documented_by(WalmartIO.bulk_product_lookup)
    async def bulk_product_lookup(self, ids:Union[str, List[str]], amount:int=20, **kwargs):
        url = self.ENDPOINT + '/affil/product/v2/items'

        params = kwargs
        ids = get_items_ids(ids)

        # Keep amount [1, 20]
        amount = min(max(1, amount), 20)

        for idGroup in self._get_product_id_chunk(list(set(ids)), amount):
            params['ids'] = idGroup
            try:
                response = await self._send_request(url, **params)
                yield [WalmartProduct(item) for item in response['items']]
            except InvalidRequestException as e:
                log.debug(f"bulk_product_lookup failed during the request with {idGroup} ids")
                log.debug(e)
            except Exception as e:
                log.error(e)

    @is_documented_by(WalmartIO.product_recommendation)
    async def product_recommendation(self, itemId:str) -> List[WalmartProduct]:
        url = url = f'{self.ENDPOINT}/affil/product/v2/nbp?itemId={itemId}'
        response = await self._send_request(url)
        return [WalmartProduct(item) for item in response] 

    @is_documented_by(WalmartIO.reviews)
    async def reviews(self, itemId:str, **kwargs) -> WalmartReviewResponse:
        if 'nextPage' in kwargs:
            page = kwargs.pop('nextPage').split('page=')[1]
            kwargs['page'] = page
        
        url = self.ENDPOINT + f'/affil/product/v2/reviews/{itemId}'
        response = await self._send_request(url, **kwargs)
        return WalmartReviewResponse(response)

    @is_documented_by(WalmartIO.search)
    async def search(self, query:str, **kwargs) -> WalmartSearch:
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
        response = await self._send_request(url, **kwargs)
        return WalmartSearch(response)

    @is_documented_by(WalmartIO.stores)
    async def stores(self, **kwargs) -> List[WalmartStore]:
        if not (('lat' in kwargs and 'lon' in kwargs) or ('zip' in kwargs)):
            raise InvalidParameterException("Missing lat & lon OR zip parameter")

        url = self.ENDPOINT + '/affil/product/v2/stores'
        response = await self._send_request(url, **kwargs)
        return [WalmartStore(store) for store in response]

    @is_documented_by(WalmartIO.taxonomy)
    async def taxonomy(self, **kwargs) -> WalmartTaxonomy:
        url = self.ENDPOINT + '/affil/product/v2/taxonomy'
        return await self._send_request(url, **kwargs)

    @is_documented_by(WalmartIO.trending)  
    async def trending(self, publisherId=None) -> List[WalmartProduct]:
        url = self.ENDPOINT + '/affil/product/v2/trends'
        
        if publisherId:
            response = await self._send_request(url, publisherId=publisherId)
        else:
            response = await self._send_request(url)
        return [WalmartProduct(item) for item in response['items']]

    @is_documented_by(WalmartIO._get_headers)
    def _get_headers(self) -> dict:
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

    @is_documented_by(WalmartIO._send_request)
    async def _send_request(self, url, **kwargs) -> dict:
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

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers(), params=request_params) as response:
                status_code = response.status
                if status_code == 200 or status_code == 201:
                    return await response.json()
                else:
                    if status_code == 400:
                        # Send exception detail when it is a 400 bad error
                        jsonData = await response.json()
                        raise InvalidRequestException(status_code, detail=jsonData['errors'][0]['message'])
                    else:
                        raise InvalidRequestException(status_code)

    @is_documented_by(WalmartIO._validate_call)
    def _validate_call(self) -> bool:
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
