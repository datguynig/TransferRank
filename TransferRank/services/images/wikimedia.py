"""Wikimedia Commons image resolver with proper attribution."""

import os
import requests
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from urllib.parse import unquote

logger = logging.getLogger(__name__)

# Simple in-memory cache for image lookups (24 hour TTL)
_image_cache = {}
CACHE_TTL = timedelta(hours=24)

def get_player_image(player_name: str) -> Optional[Dict]:
    """
    Get player image with reliable fallbacks.
    
    Returns:
        Dict with image_url, thumb_url, license, credit, source_url or None
    """
    if not player_name:
        return None
    
    # Check cache first
    cache_key = f"player_{hashlib.md5(player_name.encode()).hexdigest()}"
    if cache_key in _image_cache:
        cached_item = _image_cache[cache_key]
        if datetime.utcnow() - cached_item['cached_at'] < CACHE_TTL:
            logger.debug(f"Using cached image for {player_name}")
            return cached_item['data']
        else:
            # Remove expired cache entry
            del _image_cache[cache_key]
    
    try:
        # Use a more reliable image approach
        # Create professional football player avatar
        clean_name = player_name.replace(' ', '+')
        avatar_url = f"https://ui-avatars.com/api/?name={clean_name}&background=1e40af&color=fff&size=200&font-size=0.4&bold=true"
        
        # Test if it works
        headers = {'User-Agent': 'TransferRank/1.0'}
        response = requests.head(avatar_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            result = {
                'image_url': avatar_url,
                'thumb_url': avatar_url,
                'license': 'Generated',
                'credit': 'TransferRank',
                'source_url': avatar_url
            }
            
            # Cache the result
            _image_cache[cache_key] = {
                'data': result,
                'cached_at': datetime.utcnow()
            }
            
            logger.info(f"Generated working image for {player_name}")
            return result
        
        # Final fallback
        fallback_url = "https://via.placeholder.com/200x200/1e40af/ffffff?text=⚽"
        return {
            'image_url': fallback_url,
            'thumb_url': fallback_url,
            'license': 'Default',
            'credit': 'System Default',
            'source_url': fallback_url
        }
        
    except Exception as e:
        logger.error(f"Error getting image for {player_name}: {str(e)}")
        # Emergency fallback
        return {
            'image_url': "https://via.placeholder.com/200x200/6b7280/ffffff?text=Player",
            'thumb_url': "https://via.placeholder.com/200x200/6b7280/ffffff?text=Player",
            'license': 'Default',
            'credit': 'Default',
            'source_url': ""
        }

def get_publisher_image(domain: str) -> Optional[Dict]:
    """
    Get publisher/outlet logo from Wikimedia.
    
    Args:
        domain: Domain like 'bbc.co.uk' or 'theguardian.com'
    
    Returns:
        Dict with image_url, thumb_url, license, credit, source_url or None
    """
    if not domain:
        return None
    
    # Map common domains to Wikipedia page titles
    domain_mapping = {
        'bbc.co.uk': 'BBC Sport',
        'theguardian.com': 'The Guardian',
        'skysports.com': 'Sky Sports',
        'espn.com': 'ESPN',
        'goal.com': 'Goal.com',
        'transfermarkt.com': 'Transfermarkt'
    }
    
    page_title = domain_mapping.get(domain.lower())
    if not page_title:
        # Try to infer from domain
        if 'bbc' in domain.lower():
            page_title = 'BBC'
        elif 'guardian' in domain.lower():
            page_title = 'The Guardian'
        elif 'sky' in domain.lower():
            page_title = 'Sky Sports'
        else:
            logger.debug(f"No mapping found for domain: {domain}")
            return None
    
    try:
        image_info = get_page_images(page_title)
        if image_info:
            logger.info(f"Found Wikimedia image for {domain}")
        return image_info
        
    except Exception as e:
        logger.error(f"Error fetching Wikimedia image for {domain}: {str(e)}")
        return None

def search_wikipedia_page(search_term: str) -> Optional[str]:
    """
    Search for Wikipedia page title using OpenSearch API.
    
    Returns:
        Page title if found, None otherwise
    """
    api_url = os.environ.get('MEDIAWIKI_API', 'https://en.wikipedia.org/w/api.php')
    
    params = {
        'action': 'opensearch',
        'search': search_term,
        'limit': 5,
        'format': 'json',
        'redirects': 'resolve'
    }
    
    try:
        headers = {
            'User-Agent': 'TransferRank/1.0 (https://transferrank.com; contact@transferrank.com)'
        }
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # OpenSearch returns [query, [titles], [descriptions], [urls]]
        if len(data) >= 2 and data[1]:
            # Return first result
            return data[1][0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error searching Wikipedia for '{search_term}': {str(e)}")
        return None

def get_page_images(page_title: str) -> Optional[Dict]:
    """
    Get images from a Wikipedia page with full attribution info.
    
    Returns:
        Dict with image URLs and attribution data
    """
    api_url = os.environ.get('MEDIAWIKI_API', 'https://en.wikipedia.org/w/api.php')
    
    params = {
        'action': 'query',
        'titles': page_title,
        'prop': 'pageimages|images',
        'format': 'json',
        'piprop': 'original|thumbnail',
        'pithumbsize': 200,
        'pilimit': 1,
        'redirects': 1
    }
    
    try:
        headers = {
            'User-Agent': 'TransferRank/1.0 (https://transferrank.com; contact@transferrank.com)'
        }
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        
        for page_id, page_data in pages.items():
            if page_id == '-1':  # Page not found
                continue
            
            # Get page image info
            page_image = page_data.get('pageimage')
            if page_image:
                # Get detailed image info
                image_details = get_image_details(page_image)
                if image_details:
                    image_details['source_url'] = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                    return image_details
            
            # Fallback: try other images on the page
            images = page_data.get('images', [])
            for image in images[:3]:  # Try first 3 images
                image_title = image.get('title', '')
                if any(ext in image_title.lower() for ext in ['.jpg', '.jpeg', '.png', '.svg']):
                    image_details = get_image_details(image_title)
                    if image_details:
                        image_details['source_url'] = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                        return image_details
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting images for page '{page_title}': {str(e)}")
        return None

def get_image_details(image_title: str) -> Optional[Dict]:
    """
    Get detailed information about a specific image file.
    
    Returns:
        Dict with image_url, thumb_url, license, credit
    """
    api_url = os.environ.get('MEDIAWIKI_API', 'https://en.wikipedia.org/w/api.php')
    
    params = {
        'action': 'query',
        'titles': image_title,
        'prop': 'imageinfo',
        'iiprop': 'url|user|extmetadata',
        'iiurlwidth': 200,
        'format': 'json'
    }
    
    try:
        headers = {
            'User-Agent': 'TransferRank/1.0 (https://transferrank.com; contact@transferrank.com)'
        }
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        
        for page_id, page_data in pages.items():
            if page_id == '-1':
                continue
            
            imageinfo = page_data.get('imageinfo', [])
            if not imageinfo:
                continue
            
            info = imageinfo[0]
            
            # Extract image URLs
            image_url = info.get('url')
            thumb_url = info.get('thumburl', image_url)
            
            if not image_url:
                continue
            
            # Extract metadata
            metadata = info.get('extmetadata', {})
            
            # Get license info
            license_short = metadata.get('LicenseShortName', {}).get('value', 'Unknown')
            license_url = metadata.get('LicenseUrl', {}).get('value', '')
            
            # Get attribution info
            artist = metadata.get('Artist', {}).get('value', 'Unknown')
            credit = metadata.get('Credit', {}).get('value', artist)
            
            # Clean up HTML tags in attribution
            if credit and '<' in credit:
                import re
                credit = re.sub(r'<[^>]+>', '', credit).strip()
            
            return {
                'image_url': image_url,
                'thumb_url': thumb_url,
                'license': license_short,
                'license_url': license_url,
                'credit': credit or 'Wikimedia Commons',
                'attribution_required': True
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting details for image '{image_title}': {str(e)}")
        return None

def clear_image_cache():
    """Clear the image cache (useful for testing)."""
    global _image_cache
    _image_cache.clear()
    logger.info("Image cache cleared")