from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Count
from django.utils import timezone
import requests
import re
import logging
from .models import BlastEmail, LastVisitedUrl, ControlFlag, SkipExtension, SkipSite, VisitedUrls
from urllib.parse import urlparse
from datetime import datetime
from django.views import View


logger = logging.getLogger(__name__)
logger2 = logging.getLogger('blast_email')


def members(request):
    try:
        emails = BlastEmail.objects.filter(
            created_at__date=datetime.today(),
            status=1
        ).values(
            'email', 'id'
        ).annotate(
            occurrences=Count('email')
        ).order_by('-id')
        emails_count = BlastEmail.objects.all()
        status = ControlFlag.objects.get(id=2)
        skip_sites = list(SkipSite.objects.values_list('url', flat=True))
        skip_extensions = list(
            SkipExtension.objects.values_list('extension', flat=True))

        skip_sites_count = SkipSite.objects.count()
        skip_extensions_count = SkipExtension.objects.count()
        last_url = LastVisitedUrl.objects.latest(
            'created_at').url
        context = {
            'emails': emails,
            'last_url': last_url,
            'emails_count': emails_count,
            'status': status,
            'skip_sites': skip_sites,
            'skip_extensions': skip_extensions,
            'skip_sites_count': skip_sites_count,
            'skip_extensions_count': skip_extensions_count,
            'current_date': datetime.now(),
        }

        return render(request, 'index.html', context)
    except Exception as e:
        logger.error(f"Exception: {e}")
        return HttpResponse(f"Exception: {e}")


def hide_email(request, id):
    BlastEmail.objects.filter(id=id).update(status=False)
    return redirect('members')


def stop_crawling(request):
    ControlFlag.objects.filter(id=2).update(active=False)
    return redirect('members')


def fetch_emails(request):
    if request.method == 'POST':
        init_url = request.POST.get('url') or LastVisitedUrl.objects.filter(
            id=2).url or 'https://singroll.com/web/'

        LastVisitedUrl.objects.update_or_create(
            id=2, defaults={'url': init_url})

        collected_emails = []
        visited_urls = list(VisitedUrls.objects.values_list('url', flat=True))

        ControlFlag.objects.filter(
            id=2).update(active=True)

        crawl_page(init_url, collected_emails, visited_urls)

        ControlFlag.objects.filter(
            id=2).update(active=False)

        return redirect('members')
    return HttpResponse("Invalid request method.", status=405)


def crawl_page(url, collected_emails, visited_urls, retry_count=2):

    skip_sites = list(SkipSite.objects.values_list('url', flat=True))
    skip_extensions = list(
        SkipExtension.objects.values_list('extension', flat=True))

    if any(url.startswith(site) for site in skip_sites):
        logger2.info(f"Skipping URL: {url} as it matches skip_sites criteria.")
        return

    if any(url.endswith(extension) for extension in skip_extensions):
        logger2.info(
            f"Skipping URL: {url} as it matches skip_extensions criteria.")
        return

    if not ControlFlag.objects.get(id=2).active:
        logger2.info("Crawling stopped by user.")
        exit()

    if not url or url in visited_urls:
        return

    visited_urls.append(url)
    VisitedUrls.objects.get_or_create(url=url)
    logger2.info(f"Fetching: {url}")

    attempt = 0
    success = False

    while attempt < retry_count and not success:
        try:
            attempt += 1
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                content = response.text
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

                email_matches = re.findall(email_pattern, content)

                collected_emails = []

                for email in email_matches:
                    if not any(email.endswith(ext) for ext in skip_extensions):
                        BlastEmail.objects.get_or_create(email=email)
                        collected_emails.append(email)

                logger2.info(f"Emails found: {email_matches}")
                logger2.info(f"Emails saved: {collected_emails}")
                logger2.info(f"Stop Fetching: {url}")

                link_pattern = r'<a\s+href=["\']([^"\']+)["\']'
                link_matches = re.findall(link_pattern, content)

                for found_link in link_matches:
                    if not found_link or found_link.startswith('#'):
                        continue

                    parsed_url = urlparse(url)
                    if not re.match(r'^https?://', found_link):
                        found_link = f"{
                            parsed_url.scheme}: // {parsed_url.netloc}/{found_link.lstrip('/')}"

                    LastVisitedUrl.objects.update_or_create(
                        id=2, defaults={'url': found_link})

                    crawl_page(found_link, collected_emails, visited_urls)

                success = True
                logger2.info("Stop Fetching Process")
            else:
                logger.info(f"Failed to retrieve the page content at {
                            url} with status code: {response.status_code}")

        except requests.RequestException as e:
            logger.error(f"Attempt {attempt}: Failed to retrieve the page content at {
                         url}. Error: {e}")
            if attempt >= retry_count:
                logger.info(f"Max retry attempts reached for {
                            url}. Skipping...")
            else:
                logger.info(f"Retrying {url}... Attempt {
                            attempt} of {retry_count}")
        except Exception as e:
            logger.error(f"Attempt {attempt}: Failed to retrieve the page content at {
                         url}. Error: {e}")
            if attempt >= retry_count:
                logger.info(f"Max retry attempts reached for {
                            url}. Skipping...")
            else:
                logger.info(f"Retrying {url}... Attempt {
                            attempt} of {retry_count}")


class SkipSiteView(View):
    def post(self, request):
        url = request.POST.get('url')
        if url:
            SkipSite.objects.get_or_create(url=url)
        return redirect('members')


class SkipExtensionView(View):
    def post(self, request):
        extension = request.POST.get('extension')
        if extension:
            SkipExtension.objects.get_or_create(extension=extension)
        return redirect('members')
