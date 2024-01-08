"""Module for Walmart API responses in object form."""
from __future__ import annotations

from html import unescape
from typing import Any

__all__ = (
    "WalmartCatalog",
    "WalmartProduct",
    "WalmartTaxonomy",
    "WalmartStore",
    "WalmartSearch",
    "WalmartReview",
    "OverallRating",
    "ReviewStatistics",
    "RatingDistributions",
)


class _ResponseHandler:
    """Exposes JSON data safely to get attributes."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __str__(self) -> str:
        return str(self.payload)

    def keys(self):
        return self.payload.keys()

    def items(self):
        return self.payload.items()

    def values(self):
        return self.payload.values()

    def _get_attribute(self, attr: str) -> Any | None:
        """Attempt to get the attribute from a payload."""
        return self.payload.get(attr, None)

    def _get_attribute_text(self, attr: str) -> str | None:
        """Get clean unescaped html text."""
        try:
            return unescape(self.payload.get(attr, None))
        except TypeError:
            return None

    def _get_attribute_float(self, attr: str) -> float | None | Any:
        """Safe extraction of a float attribute from the payload."""
        try:
            return float(self.payload.get(attr, None))
        except ValueError:
            return self.payload.get(attr, None)

    def _get_attribute_int(self, attr: str) -> int | None | Any:
        """Safe extraction of an int attribute from the payload."""
        try:
            return int(self.payload.get(attr, None))
        except ValueError:
            return self.payload.get(attr, None)


class _WalmartResponse:
    """Base class for Walmart responses."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.response_handler = _ResponseHandler(payload)

    def __str__(self) -> str:
        return str(self.response_handler)

    def __getitem__(self, key):
        return self.response_handler._get_attribute(key)

    def get_attr(self, attr: str):
        """Another way to get attributes.

        The function call helps in case an attribute is added to Walmart API but not here.

        Parameters
        ----------
        attr: str
            JSON attribute to get from product response
        """
        return self.response_handler._get_attribute(attr)

    def keys(self):
        return self.response_handler.keys()

    def items(self):
        return self.response_handler.items()

    def values(self):
        return self.response_handler.values()


class WalmartProduct(_WalmartResponse):
    """A Walmart Products as an object.

    Not all properties exist for all products. To get a more in-depth look, visit
    (https://walmart.io/docs/affiliate/item_response_groups)

    Each property of this class will safely return a value or `None` if the product does not have
    that attribute.

    Base Responses are Marked by `Base Response`
    """

    @property
    def itemId(self):
        """A positive integer that uniquely identifies an item.

        `Base Response`
        """
        return self.response_handler._get_attribute_int("itemId")

    @property
    def parentItemId(self):
        """Item Id of the base version for this item.

        This is present only if item is a variant of the base version,
        such as a different color or size.
        """
        return self.response_handler._get_attribute_int("parentItemId")

    @property
    def name(self):
        """Standard name of the item.

        `Base Response`
        """
        return self.response_handler._get_attribute("name")

    @property
    def msrp(self):
        """Manufacturer suggested retail price.

        `Base Response`
        """
        return self.response_handler._get_attribute("msrp")

    @property
    def salePrice(self):
        """Selling price for the item in USD.

        `Base Response`
        """
        return self.response_handler._get_attribute_float("salePrice")

    @property
    def upc(self):
        """Unique Product Code.

        `Base Response`
        """
        return self.response_handler._get_attribute("upc")

    @property
    def categoryPath(self):
        """Breadcrumb for the item.

        This string describes the category level hierarchy that the item falls under.

        `Base Response`
        """
        return self.response_handler._get_attribute("categoryPath")

    @property
    def categoryNode(self):
        """Category id for the category of this item.

        This value can be passed to APIs to pull this item's category level information.
        """
        return self.response_handler._get_attribute("categoryNode")

    @property
    def shortDescription(self):
        """Short description for the item."""
        return self.response_handler._get_attribute_text("shortDescription")

    @property
    def longDescription(self):
        """Long description for the item.

        `Base Response`
        """
        return self.response_handler._get_attribute("longDescription")

    @property
    def brandName(self):
        """Item's brand."""
        return self.response_handler._get_attribute("brandName")

    @property
    def thumbnailImage(self):
        """Small size image for the item in jpeg format with dimensions 100 x 100 pixels.

        Returns URL of image

        `Base Response`
        """
        return self.response_handler._get_attribute("thumbnailImage")

    @property
    def mediumImage(self):
        """Medium size image for the item in jpeg format with dimensions 180 x 180 pixels.

        Returns URL of image
        """
        return self.response_handler._get_attribute("mediumImage")

    @property
    def largeImage(self):
        """Large size image for the item in jpeg format with dimensions 450 x 450 pixels.

        Returns URL of image
        """
        return self.response_handler._get_attribute("largeImage")

    @property
    def productTrackingUrl(self):
        """Affiliate URL.

        Deep linked URL that directly links to the product page of this item on walmart.com, and
        uniquely identifies the affiliate sending this request via a impact radius tracking id
        |PUBID|. The PUBID parameter needs to be replaced with your impact radius tracking id,
        and is used by Walmart to correctly attribute the sales from your channel on walmart.com.
        Actual commission numbers will be made available through your impact radius account.

        `Base Response`
        """
        return self.response_handler._get_attribute("productTrackingUrl")

    @property
    def ninetySevenCentShipping(self):
        """Whether the item qualifies for 97 cent shipping.

        Returns
        -------
        Bool
        """
        return self.response_handler._get_attribute("ninetySevenCentShipping")

    @property
    def standardShipRate(self):
        """Shipping rate for this item for standard shipping (3 to 5 business days).

        `Base Response`
        """
        return self.response_handler._get_attribute("standardShipRate")

    @property
    def twoThreeDayShippingRate(self):
        """Expedited shipping rate for this item (2 to 3 business days)."""
        return self.response_handler._get_attribute("twoThreeDayShippingRate")

    @property
    def size(self):
        """Size attribute for the item."""
        return self.response_handler._get_attribute("size")

    @property
    def color(self):
        """Color attribute for the item."""
        return self.response_handler._get_attribute("color")

    @property
    def marketplace(self):
        """Whether this item is from one of the Walmart marketplace sellers.

        In this case, the item cannot be returned back to Walmart stores or walmart.com.
        It must be returned to the marketplace seller in accordance with their returns policy.

        `Base Response`
        """
        return self.response_handler._get_attribute("marketplace")

    @property
    def sellerInfo(self):
        """Name of the marketplace seller, applicable only for marketplace items."""
        return self.response_handler._get_attribute("sellerInfo")

    @property
    def shipToStore(self):
        """Whether the item can be shipped to the nearest Walmart store."""
        return self.response_handler._get_attribute("shipToStore")

    @property
    def freeShipToStore(self):
        """Whether the item qualifies for free shipping to the nearest Walmart store.

        Returns
        -------
        Bool
        """
        return self.response_handler._get_attribute("freeShipToStore")

    @property
    def modelNumber(self):
        """Model number attribute for the item."""
        return self.response_handler._get_attribute("modelNumber")

    @property
    def availableOnline(self):
        """Whether the item is currently available for sale on Walmart.com.

        `Base Response`
        """
        return self.response_handler._get_attribute("availableOnline")

    @property
    def stock(self):
        """Indicative quantity of the item available online.

        Possible values are [Available, Limited Supply, Last few items, Not available].
         * Limited supply: can go out of stock in the near future,
            so needs to be refreshed for availability more frequently.
         * Last few items: can go out of stock very quickly,
            so could be avoided in case you only need to show available items to your users.
        """
        return self.response_handler._get_attribute("stock")

    @property
    def customerRating(self):
        """Average customer rating out of 5."""
        return self.response_handler._get_attribute_float("customerRating")

    @property
    def numReviews(self):
        """Number of customer reviews available on this item on Walmart.com."""
        return self.response_handler._get_attribute_int("numReviews")

    @property
    def clearance(self):
        """Whether the item is on clearance on Walmart.com."""
        return self.response_handler._get_attribute("clearance")

    @property
    def preOrder(self):
        """Whether this item is available on pre-order on Walmart.com."""
        return self.response_handler._get_attribute("preOrder")

    @property
    def preOrderShipsOn(self):
        """Date the item will ship on if it is a pre-order item."""
        return self.response_handler._get_attribute("preOrderShipsOn")

    @property
    def offerType(self):
        """Indicates whether the item is sold ONLINE_ONLY, ONLINE_AND_STORE, STORE_ONLY.

        `Base Response`
        """
        return self.response_handler._get_attribute("offerType")

    @property
    def rhid(self):
        """Indicates the offer category id for this item."""
        return self.response_handler._get_attribute("rhid")

    @property
    def bundle(self):
        """Indicates if the item is a bundle."""
        return self.response_handler._get_attribute("bundle")

    @property
    def attributes(self):
        """Various attributes for the item."""
        return self.response_handler._get_attribute("attributes")

    @property
    def affiliateAddToCartUrl(self):
        """Affiliate Url for directly sending user to cart.

        Impact Radius tracking url to add the item on Walmart.com cart page and uniquely identifies
        the affiliate via a impact radius tracking id. The impact radius tracking id is used by
        Walmart to correctly attribute the sales from your channel on walmart.com. Actual
        commission numbers will be made available through your impact radius account.
        """
        return self.response_handler._get_attribute("affiliateAddToCartUrl")

    @property
    def freeShippingOver35Dollars(self):
        """Indicates if the item is eligible for free shipping over 35 dollars."""
        return self.response_handler._get_attribute("freeShippingOver35Dollars")

    @property
    def gender(self):
        """Indicates the gender for the item."""
        return self.response_handler._get_attribute("gender")

    @property
    def age(self):
        """Indicates the age range for the item."""
        return self.response_handler._get_attribute("age")

    @property
    def imageEntities(self):
        """Primary and secondary images of the item on Walmart.com.

        Each image are in thumbnail, medium and large sizes

        `Base Response`
        """
        return self.response_handler._get_attribute("imageEntities")

    @property
    def isTwoDayShippingEligible(self):
        """Indicates whether the item is eligible for two day shipping.

        `Base Response`
        """
        return self.response_handler._get_attribute("isTwoDayShippingEligible")

    @property
    def customerRatingImage(self):
        """Image of average customer rating."""
        return self.response_handler._get_attribute("customerRatingImage")

    @property
    def giftOptions(self):
        """Indicates the gift options of the item.

        Whether gift wrap, gift message, gift receipt are allowed.

        `Base Response`
        """
        return self.response_handler._get_attribute("giftOptions")

    @property
    def bestMarketplacePrice(self):
        """Information about best price on marketplace.

        Including:
            price, sellerInfo, standardShipRate, twoThreeDayShippingRate, availableOnline,
            clearance, and offerType
        """
        return self.response_handler._get_attribute("bestMarketplacePrice")

    @property
    def variants(self):
        """The itemIds of the item's variants, if variants exist."""
        return self.response_handler._get_attribute("variants")


# hi :p


class WalmartCatalog(_WalmartResponse):
    """Walmart Catalog Products response object."""

    @property
    def category(self):
        """Category id of the desired category. This should match the id field from Taxonomy API."""
        return self.response_handler._get_attribute("category")

    @property
    def format(self):  # noqa: A003
        """Format of response. Should be json."""
        return self.response_handler._get_attribute("format")

    @property
    def nextPage(self):
        """URI of next page.

        Pass this back into `catalog_product` as `nextPage=data.nextPage` to get next page response.
        """
        return self.response_handler._get_attribute("nextPage")

    @property
    def nextPageExist(self) -> bool:
        """Boolean of if there is a next page."""
        return self.response_handler._get_attribute("nextPageExist")  # type: ignore

    @property
    def totalPages(self):
        """Amount of pages that fit the category."""
        return self.response_handler._get_attribute("totalPages")

    @property  # type: ignore
    def items(self) -> list[WalmartProduct]:
        """List of Walmart items returned from the response."""
        r = self.response_handler._get_attribute("items") or []
        return [WalmartProduct(item) for item in r]


class WalmartReview(_WalmartResponse):
    """Walmart reviews object."""

    @property
    def name(self):
        """Standard name of the item."""
        return self.response_handler._get_attribute("name")

    @property
    def overallRating(self):
        """`OverallRating` for the rating of the item overallRating."""
        return OverallRating(self.response_handler._get_attribute("overallRating"))  # type: ignore

    @property
    def reviewer(self):
        """Reviewer's Name."""
        return self.response_handler._get_attribute("reviewer")

    @property
    def reviewText(self):
        """Customer review text."""
        return self.response_handler._get_attribute("reviewText")

    @property
    def submissionTime(self):
        """Timestamp at which customer submitted review."""
        return self.response_handler._get_attribute("submissionTime")

    @property
    def title(self):
        """Title of review."""
        return self.response_handler._get_attribute("title")

    @property
    def upVotes(self):
        """Count of up votes given to customer review."""
        return self.response_handler._get_attribute("upVotes")

    @property
    def downVotes(self):
        """Count of down votes given to customer review."""
        return self.response_handler._get_attribute("downVotes")


class OverallRating(_WalmartResponse):
    """Overall rating of a product."""

    @property
    def label(self):
        """Type of rating."""
        return self.response_handler._get_attribute("label")

    @property
    def rating(self):
        """Customer rating."""
        return self.response_handler._get_attribute("rating")


class RatingDistributions(_WalmartResponse):
    """Rating distribution of reviews for Walmart products."""

    @property
    def ratingValue(self):
        """Rating distribution for the rating value."""
        return self.response_handler._get_attribute("ratingValue")

    @property
    def count(self):
        """Count of customer ratings for rating of ratingValue."""
        return self.response_handler._get_attribute("count")


class ReviewStatistics(_WalmartResponse):
    """Statistics of a products reviews."""

    @property
    def averageOverallRating(self):
        """Overall customer rating for the item."""
        return self.response_handler._get_attribute("averageOverallRating")

    @property
    def overallRatingRange(self):
        """Range of the customer rating."""
        return self.response_handler._get_attribute("overallRatingRange")

    @property
    def ratingDistributions(self) -> list[RatingDistributions]:
        """Customer Rating Distribution."""
        response = self.response_handler._get_attribute("ratingDistributions") or []
        return [RatingDistributions(dist) for dist in response]

    @property
    def totalReviewCount(self):
        """Total no of customer reviews."""
        return self.response_handler._get_attribute("totalReviewCount")


class WalmartReviewResponse(_WalmartResponse):
    """The entire response from https://walmart.io/docs/affiliate/reviews API call."""

    @property
    def itemId(self):
        """Item Id."""
        return self.response_handler._get_attribute("itemId")

    @property
    def name(self):
        """Standard name of the item."""
        return self.response_handler._get_attribute("name")

    @property
    def salePrice(self):
        """Sales Price of the item."""
        return self.response_handler._get_attribute("salePrice")

    @property
    def upc(self):
        """Unique Product Code."""
        return self.response_handler._get_attribute("upc")

    @property
    def categoryPath(self):
        """This string describes the Reporting Hierarchy level names that the item falls under."""  # noqa: D404
        return self.response_handler._get_attribute("categoryPath")

    @property
    def brandName(self):
        """Item's brand."""
        return self.response_handler._get_attribute("brandName")

    @property
    def productTrackingUrl(self):
        """Product's tracking URL using publisher id."""
        return self.response_handler._get_attribute("productTrackingUrl")

    @property
    def categoryNode(self):
        """This string describes the Reporting Hierarchy level Ids that the item falls under."""  # noqa: D404
        return self.response_handler._get_attribute("categoryNode")

    @property
    def reviews(self) -> list[WalmartReview]:
        """Array of `WalmartReview` reviews for the item."""
        response = self.response_handler._get_attribute("reviews") or []
        return [WalmartReview(review) for review in response]

    @property
    def reviewStatistics(self) -> ReviewStatistics:
        """Customer review stats for the item."""
        return ReviewStatistics(self.response_handler._get_attribute("reviewStatistics"))  # type: ignore

    @property
    def nextPage(self):
        """URL next page of customer Review."""
        return self.response_handler._get_attribute("nextPage")

    @property
    def availableOnline(self) -> bool:
        """Item available online (true/false)."""
        return self.response_handler._get_attribute("availableOnline")  # type: ignore


class WalmartStore(_WalmartResponse):
    """Walmart Store container from search API (store)."""

    @property
    def no(self):
        """Store number."""
        return self.response_handler._get_attribute_int("no")

    @property
    def name(self):
        """Name."""
        return self.response_handler._get_attribute("name")

    @property
    def country(self):
        """Country."""
        return self.response_handler._get_attribute("country")

    @property
    def coordinates(self) -> list[float]:
        """Coordinates Array."""
        return self.response_handler._get_attribute("coordinates") or []

    @property
    def streetAddress(self):
        """Street Address."""
        return self.response_handler._get_attribute("streetAddress")

    @property
    def city(self):
        """City."""
        return self.response_handler._get_attribute("city")

    @property
    def stateProvCode(self):
        """State Province Code."""
        return self.response_handler._get_attribute("stateProvCode")

    @property
    def zip(self):  # noqa: A003
        """Zip Code."""
        return self.response_handler._get_attribute("zip")

    @property
    def phoneNumber(self):
        """Store's Phone Number."""
        return self.response_handler._get_attribute("phoneNumber")


class WalmartSearch(_WalmartResponse):
    """Response from Walmart Search API."""

    @property
    def query(self):
        """Search text - whitespace separated sequence of keywords to search for."""
        return self.response_handler._get_attribute("query")

    @property
    def sort(self):
        """Sort type - [relevance, price, title, bestseller, customerRating, new]."""
        return self.response_handler._get_attribute("sort")

    @property
    def responseGroup(self):
        """[base, full] Item Response Groups type."""
        return self.response_handler._get_attribute("responseGroup")

    @property
    def totalResults(self):
        """Int of amount of items in search."""
        return self.response_handler._get_attribute_int("totalResults")

    @property
    def start(self):
        """Starting point of the results within the matching set of items."""
        return self.response_handler._get_attribute("start")

    @property
    def numItems(self):
        """Number of matching items to be returned, max value 25."""
        return self.response_handler._get_attribute_int("numItems")

    @property  # type: ignore
    def items(self) -> list[WalmartProduct]:
        """List[`WalmartProduct`]."""
        response = self.response_handler._get_attribute("items") or []
        return [WalmartProduct(item) for item in response]

    @property
    def facets(self):
        """The facets for the search."""
        return self.response_handler._get_attribute("facets")


class WalmartTaxonomy(_WalmartResponse):
    """Taxonomy used to categorize items on Walmart.com."""

    @property
    def id(self):  # noqa: A003
        """Category id for this category.

        These values are used as an input parameter to other APIs.
        """
        return self.response_handler._get_attribute("id")

    @property
    def name(self):
        """Name for this category as specified on Walmart.com."""
        return self.response_handler._get_attribute("name")

    @property
    def children(self):
        """List of categories that have the current category as a parent in the taxonomy."""
        response = self.response_handler._get_attribute("children") or []
        return [WalmartTaxonomy(child) for child in response]

    @property
    def path(self):
        """Category path for this category."""
        return self.response_handler._get_attribute("path")
