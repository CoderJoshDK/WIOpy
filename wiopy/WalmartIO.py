"""Walmart IO Sync API.

Please read the Walmart Docs for up to date list of endpoints and parameters
"""
from __future__ import annotations

import base64
import datetime
import logging
import time
from typing import Any, Generator

import requests
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from .utils import InvalidRequestException, _get_items_ids, _ttl_cache
from .WalmartResponse import (
    WalmartCatalog,
    WalmartProduct,
    WalmartReviewResponse,
    WalmartSearch,
    WalmartStore,
    WalmartTaxonomy,
)

log = logging.getLogger(__name__)
log.setLevel("DEBUG")

__all__ = ("WalmartIO",)


# Affiliates API only
class WalmartIO:
    """The main Walmart IO API interface.

    Optional:
    -------
    You can provide `daily_calls` if it is not the default 5000.
    publisherId can also be provided and it will auto populate every query.
    If you give publisherId as a kwarg, it will override the default one the class has

    Examples
    --------
    >>> walmart_io = WalmartIO(
    ...         private_key_version='1',
    ...         private_key_filename='./WM_IO_private_key.pem',
    ...         consumer_id='XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
    ...     )
    """

    __slots__ = (
        "_private_key_version",
        "_private_key",
        "_consumer_id",
        "headers",
        "_update_daily_calls_time",
        "daily_calls",
        "daily_calls_remaining",
        "publisherId",
    )

    ENDPOINT = "https://developer.api.walmart.com/api-proxy/service"

    def __init__(
        self,
        *,
        private_key_version: str = "1",
        private_key_filename: str,
        consumer_id: str,
        daily_calls: int = 5000,
        publisherId: str | None = None,
    ) -> None:
        """WalmartIO API Connection.

        Parameters
        ----------
        private_key_version: str, default="1", optional
            The version of the private key.
        consumer_id: str
            The UUID generated for the client application
        private_key_filename: str
            The file with the private key.
        daily_calls: int, default=5000
            Walmart grants 5000 daily calls to their API but you can ask for more.
             It can be assumed that this object will exist over multiple days,
            so total calls made in a day will be limited.
            https://walmart.io/termsandcondition
        publisherId: str, optional
            Your Impact Radius Publisher Id.
            If provided, it will auto populate every query with your id

        Notes
        -----
        To Generate the public and private key (https://walmart.io/key-tutorial).
        The filename will look something like `./WM_IO_private_key.pem`
        """
        self._private_key_version = private_key_version

        # IOError is triggered if the file cannot be opened
        with open(private_key_filename) as f:
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
        """Catalog Product Endpoint.

        Allows a developer to retrieve the products catalog in a paginated fashion.
        Catalog can be filtered by category, brand and/or any special offers like rollback,
        clearance etc.

        Parameters
        ----------
        **kwargs: dict
            publisherId:
                Your Impact Radius id.
                 If passed, this value will be set in the affiliate links in the response
            adId:
                Your Impact Radius Advertisement Id
            campaignId:
                Your Impact Radius Campaign Id
            category:
                Category id of the desired category.
                 This should match the id field from Taxonomy API
            brand:
                Brand name
            specialOffer:
                Special offers like rollback, clearance, specialBuy
            soldByWmt:
                Set it to true if you only want items sold by Walmart.com
                 (excluding marketplace items)
            available:
                Set it to true if you only want items that are available to purchase
                 (excluding out of stock items)
            count:
                Number of items the API will return

        Notes
        -----
        It is recommend passing category or brand as query parameters for faster response times

        References
        ----------
        https://www.walmart.io/docs/affiliate/catalog-product
        """
        if "nextPage" in kwargs:
            url = "https://developer.api.walmart" + kwargs.pop("nextPage")
        else:
            url = self.ENDPOINT + "/affil/product/v2/paginated/items"

        response = self._send_request(url, **kwargs)
        return WalmartCatalog(response)

    def post_browsed_products(self, itemId: str) -> list[WalmartProduct]:
        """Post Browsed Products Endpoint.

        Allows you to recommend products to someone based on their product viewing history.

        Similar to the Product Recommendation API, this endpoint uses one item ID as the anchor
        for the output. For instance, if you know that one of your customers has recently viewed an
        Xbox one, it is likely that they may be also interested in purchasing a PlayStation 4, or
        Nintendo Wii.

        Some example use cases for this data:
        Re-targeting to your customers based on knowing their recent viewing history.
        Understanding what other similar items a customer might purchase if the initial item
           they were interested in has gone out of stock.

        Parameters
        ----------
        itemId : str
            Each item on Walmart.com has a particular item ID associated with it.
            This can be generally seen in the last 8 digits of a URL string, but can also be
            acquired by using the Product Lookup API.

        Returns
        -------
        list of WalmartProduct
            The endpoint returns a maximum of 10 `WalmartProduct`s, being ordered from most
            relevant to least relevant for the customer.

        References
        ----------
        https://www.walmart.io/docs/affiliate/post-browsed-products
        """
        url = f"{self.ENDPOINT}/affil/product/v2/postbrowse?itemId={itemId}"
        response = self._send_request(url)
        return [WalmartProduct(item) for item in response]

    def product_lookup(self, ids: str | list[str], **kwargs) -> list[WalmartProduct]:
        """Walmart product lookup.

        For more info: (https://walmart.io/docs/affiliate/product-lookup)

        Parameters
        ----------
        ids : str or list of str
            list of ids to lookup
        **kwargs: dict, optional
             publisherId:
                Your Impact Radius Publisher Id
             adId:
                Your Impact Radius Advertisement Id
             campaignId:
                Your Impact Radius Campaign Id
             upc:
                upc of the item

        Returns
        -------
        products: list of `WalmartProduct`
            List[ https://walmart.io/docs/affiliate/item_response_groups ]

        References
        ----------
        https://www.walmart.io/docs/affiliate/product-lookup
        """
        url = self.ENDPOINT + "/affil/product/v2/items"

        params = kwargs
        ids = _get_items_ids(ids)
        if len(ids) > 200:
            log.debug(
                "For large id lists, try using bulk_product_lookup."
                "It will continue to run even if one chunk of ids raise an error"
            )
        products = []

        for idGroup in self._get_product_id_chunk(list(set(ids)), 20):
            params["ids"] = idGroup
            response = self._send_request(url, **params)
            for item in response["items"]:
                products.append(WalmartProduct(item))

        return products

    def bulk_product_lookup(
        self, ids: str | list[str], amount: int = 20, retries: int = 1, **kwargs
    ):
        """Walmart product lookup for a bulk of products.

        It will keep going even if there are errors
        This function is a generator that gives you #amount products at a time

        For more info: (https://walmart.io/docs/affiliate/product-lookup)

        Parameters
        ----------
        ids: str or list of str
            ids to lookup
        amount: int, default=20
            the amount of products to yield at a time (max 20)
        retries: int, default=1
            the amount of times to retry an chunk, on error from server
        **kwargs: dict
             publisherId:
                Your Impact Radius Publisher Id
             adId:
                Your Impact Radius Advertisement Id
             campaignId:
                Your Impact Radius Campaign Id
             format:
                Type of response required, allowed values [json, xml(deprecated)]. Default is json.
             upc:
                upc of the item

        Yields
        ------
        list of WalmartProduct
            List[ https://walmart.io/docs/affiliate/item_response_groups ]

        See Also
        --------
        WalmartIO.product_lookup: look up that will raise errors given from response

        References
        ----------
        https://www.walmart.io/docs/affiliate/product-lookup
        """
        url = self.ENDPOINT + "/affil/product/v2/items"

        params = kwargs
        ids = _get_items_ids(ids)

        # Clamp amount [1, 20]
        amount = min(max(1, amount), 20)

        for idGroup in self._get_product_id_chunk(list(set(ids)), amount):
            params["ids"] = idGroup
            for attempt in range(retries):
                try:
                    response = self._send_request(url, **params)
                    yield [WalmartProduct(item) for item in response["items"]]
                    break
                except InvalidRequestException as e:
                    if attempt == retries - 1:
                        log.debug(
                            f"bulk_product_lookup failed during the request with {idGroup} ids"
                        )
                        log.debug(e)

    def product_recommendation(self, itemId: str) -> list[WalmartProduct]:
        """Product Recommendation Endpoint.

        Extension driven by the science that powers the recommended products container on
        Walmart.com. Walmart has parsed 100s of millions of transactions over their product
        catalog of more than 6 million products to be able to deliver, with accuracy,
        the items in this response. Some example use cases where a partner might be interested
        in utilizing this data:
         * A recommended products advertising widget via e-mail delivered right after a
            transaction has been verified
         * Re-targeting on an e-commerce storefront anchored on a shared UPC between
            multiple merchants
         * An up-sell to an existing customer presenting an array of products due to knowing
            their order history

        Parameters
        ----------
        itemId: str
            Each item on Walmart.com has a particular item ID associated with it.
            This can be generally seen in the last 8 digits of a URL string, but can also be
            acquired by using the Product Lookup API.

        Returns
        -------
        list of WalmartProduct:
            The endpoint returns a maximum of 10 `WalmartProduct`s, being ordered from most
            relevant to least relevant for the customer.

        References
        ----------
        https://www.walmart.io/docs/affiliate/product-recommendation
        """
        url = f"{self.ENDPOINT}/affil/product/v2/nbp?itemId={itemId}"
        response = self._send_request(url)
        return [WalmartProduct(item) for item in response]

    def reviews(self, itemId: str, **kwargs) -> WalmartReviewResponse:
        """Reviews Endpoint.

        Gives you access to the extensive item reviews on Walmart that have been written by the
        users of Walmart.com. This is great content for enriching item descriptions. You are free
        to showcase this content on your application provided you link back to the original
        content page on Walmart.com, as specified in the response parameter "productTrackingUrl".
        (https://walmart.io/docs/affiliate/reviews).

        Parameters
        ----------
        itemId: str
            the id of the item to query for its reviews
        **kwargs
             publisherId:
                Impact Radius Publisher Id
             nextPage:
                    Next Page of customer reviews. The value is available in previous response to
                    the api call.

        Returns
        -------
        review (`WalmartReview`) : Walmart review object

        References
        ----------
        https://www.walmart.io/docs/affiliate/product-recommendation
        """
        if "nextPage" in kwargs:
            page = kwargs.pop("nextPage").split("page=")[1]
            kwargs["page"] = page

        url = self.ENDPOINT + f"/affil/product/v2/reviews/{itemId}"
        response = self._send_request(url, **kwargs)
        return WalmartReviewResponse(response)

    def search(self, query: str, **kwargs) -> WalmartSearch:
        """Search Endpoint.

        Text search on the Walmart.com catalog and returns matching items available for sale online.

        Item results returned by the API are paginated, with up to 25 items displayed per page
        (using the numItems parameter). It is possible to request more by using the "start"
        parameter that specifies the first item number in the response. Pagination is limited to
        the top 1000 items for a particular search.

        Items are sorted by a user-specified order.
        The default sort is by relevance.
        Please see below for a list of available sort types.

        Parameters
        ----------
        query: str
            Search text - white space separated sequence of keywords to search for
        **kwargs
             publisherId:
                Your Impact Radius Publisher Id
             categoryId:
                Category id of the category for search within a category. This should match the id
                field from Taxonomy API
             start:
                Starting point of the results within the matching set of items - up to 10 items
                will be returned starting from this item
             sort:
                Sorting criteria, allowed sort types are [relevance, price, title, bestseller,
                customerRating, new]. Default sort is by relevance.
             order:
                Sort ordering criteria, allowed values are [ascending, descending].
                This parameter is needed only for the sort types [price].
             numItems:
                Number of matching items to be returned, max value 25. Default is 10.
             responseGroup:
                Specifies the item fields returned in the response, allowed response groups are
                [base, full]. Default value is base. Refer Item Response Groups for details of
                exact fields returned by each response group.
             facet:
                Flag to enable facets. Default value is off. Set this to on to enable facets.
             facet.filter:
                Filter on the facet attribute values. This parameter can be set to
                <facet-name>:<facet-value> (without the angles). Here facet-name and facet-value
                can be any valid facet picked from the search API response when facets are on.
             facet.range:
                Range filter for facets which take range values, like price. See usage above in
                the examples.

        Returns
        -------
        WalmartSearch: Walmart Search object

        References
        ----------
        https://walmart.io/docs/affiliate/search
        """
        if "facet" in kwargs:
            facet = kwargs["facet"]
            if isinstance(facet, bool):
                kwargs["facet"] = "on" if facet else "off"

        if "range" in kwargs:
            kwargs["facet.range"] = kwargs.pop("range")
            kwargs["facet"] = "on"
        if "filter" in kwargs:
            kwargs["facet.filter"] = kwargs.pop("filter")
            kwargs["facet"] = "on"

        kwargs["query"] = query

        url = self.ENDPOINT + "/affil/product/v2/search"
        response = self._send_request(url, **kwargs)
        return WalmartSearch(response)

    def stores(self, **kwargs) -> list[WalmartStore]:
        """Store Locator Endpoint.

        Locate nearest Walmart Stores via API. It lets users search for stores by
        latitude and longitude, and by zip code.

        Params (optional):
        -------
        **kwargs:
            lat : Latitude
            lon : Longitude
            zip : Zip

        Returns
        -------
        store ('WalmartStore') : closest store to specified location
        """
        if not (("lat" in kwargs and "lon" in kwargs) or ("zip" in kwargs)):
            raise ValueError("Missing lat & lon OR zip parameter")

        url = self.ENDPOINT + "/affil/product/v2/stores"
        response = self._send_request(url, **kwargs)
        return [WalmartStore(store) for store in response]

    def taxonomy(self, **kwargs) -> WalmartTaxonomy:
        """Taxonomy Endpoint.

        Taxonomy used to categorize items on Walmart.com.

        The Taxonomy API exposes the category taxonomy used by Walmart.com to categorize items.
        It describes three levels: Departments, Categories and Sub-categories as available on
        Walmart.com. It is possible to specify the exact category as a parameter when using any of
        the API's below:
        * Search
        * Catalog Product

        For example, Search API can be restricted to search within a category by supplying id as
        per the taxonomy.

        Parameters
        ----------
        **kwargs
            unknown; WalmartIO documentation does not expose what the acceptable
        """
        url = self.ENDPOINT + "/affil/product/v2/taxonomy"
        return WalmartTaxonomy(self._send_request(url, **kwargs))

    def trending(self, publisherId=None) -> list[WalmartProduct]:
        """Trending Items Endpoint.

        The Trending Items API is designed to give the information on what is bestselling on
        Walmart.com right now. The items returned by this service are a curated list based on the
        collective browsing and sales activity of all of Walmart's users. The data for this
        services is updated multiple times a day. You can expect a high click through and
        conversion rate on these items if you choose to advertise them.

        Parameters
        ----------
        publisherId: str
            Your Impact Radius Publisher Id

        Returns
        -------
        products: list of `WalmartProduct`
            a list of walmart products on the trending list
        """
        url = self.ENDPOINT + "/affil/product/v2/trends"

        if publisherId:
            response = self._send_request(url, publisherId=publisherId)
        else:
            response = self._send_request(url)
        return [WalmartProduct(item) for item in response["items"]]

    @_ttl_cache(maxsize=2, ttl=170)
    def _get_headers(self) -> dict:
        """Get the headers required for making an API call.

        References
        ----------
        https://walmart.io/docs/affiliate/onboarding-guide

        Returns
        -------
        headers: {
             'WM_CONSUMER.ID' : consumerId,
             'WM_CONSUMER.INTIMESTAMP' : epoxTime,
             'WM_SEC.AUTH_SIGNATURE' : signature_enc,
             'WM_SEC.KEY_VERSION' : keyVersion
         }
        """
        timeInt = int(time.time() * 1000)

        self.headers["WM_CONSUMER.INTIMESTAMP"] = str(timeInt)

        # <--- WM_SEC.AUTH_SIGNATURE --->
        # The signature generated using the private key and signing the values of consumer id,
        # timestamp and key version. The TTL of this signature is 180 seconds. Post that,
        # the API Proxy will throw a "timestamp expired" error.

        sortedHashString = (
            self.headers["WM_CONSUMER.ID"]
            + "\n"
            + self.headers["WM_CONSUMER.INTIMESTAMP"]
            + "\n"
            + self.headers["WM_SEC.KEY_VERSION"]
            + "\n"
        )
        encodedHashString = sortedHashString.encode()

        hasher = SHA256.new(encodedHashString)
        signer = PKCS1_v1_5.new(self._private_key)
        signature = signer.sign(hasher)
        signature_enc = str(base64.b64encode(signature), "utf-8")

        self.headers["WM_SEC.AUTH_SIGNATURE"] = signature_enc

        return self.headers

    def _send_request(self, url, **kwargs) -> Any:
        """Send a request to the Walmart API and return the HTTP response.

        Format is json by default and cannot be changed through kwargs. xml is deprecated.
        Send richAttributes='true' by default. Can be set to 'false' through kwargs

        Parameters
        ----------
        url: str
            The endpoint url to make the request
        **kwargs: dict
            Any of the optional GET arguments specified in the Walmart specification

        Returns
        -------
        response : HTTP response from url

        Errors:
        -------
        InvalidRequestException:
            If the response's status code is different than 200 or 201,
            raise an InvalidRequestException with the appropriate code
        """
        log.debug(f"Making connection to {url}")

        # Avoid format to be changed, always go for json
        kwargs.pop("format", None)
        request_params = kwargs

        # Convert from native boolean python type to string 'true' or 'false'.
        # This allows to set richAttributes with python boolean types
        if "richAttributes" in request_params and isinstance(
            request_params["richAttributes"], bool
        ):
            if request_params["richAttributes"]:
                request_params["richAttributes"] = "true"
            else:
                request_params["richAttributes"] = "false"
        else:
            # Even if not specified in arguments, send request with richAttributes='true' by default
            request_params["richAttributes"] = "true"

        if self.publisherId and "publisherId" not in request_params:
            request_params["publisherId"] = self.publisherId

        if not self._validate_call():
            log.warning(
                "Too many calls in one day. If this is incorrect, try increasing `daily_calls`"
            )

        response = requests.get(url, headers=self._get_headers(), params=request_params)
        if response.status_code in (200, 201):
            return response.json()

        if response.status_code == 400:
            # Send exception detail when it is a 400 bad error
            raise InvalidRequestException(
                response.status_code, detail=response.json()["errors"][0]["message"]
            )

        raise InvalidRequestException(response.status_code)

    def _validate_call(self) -> bool:
        """Check if the caller has API calls remaining.

        If there are remaining calls, check to see if the headers need to be updated.
        If so, update them.

        Returns
        -------
        bool:
            if there are still remaining calls for the day
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
    def _get_product_id_chunk(full_list: list[str], chunk_size: int) -> Generator[str, None, None]:
        """Yield successive chunks from List."""
        for i in range(0, len(full_list), chunk_size):
            yield ",".join(full_list[i : i + chunk_size])
