import logging
import time
from socket import socket
import aiofiles
from pyquery import PyQuery as pq
import re
from os.path import exists, getsize
from os import makedirs
import aiohttp
import asyncio
import socket
from urllib3.connection import HTTPConnection

HTTPConnection.default_socket_options = (
        HTTPConnection.default_socket_options + [
    (socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000),  # 1MB in byte
    (socket.SOL_SOCKET, socket.SO_RCVBUF, 1000000)
])


# set logging config
logging.basicConfig(level=logging.INFO,
                     format='%(asctime)s - %(levelname)s : %(message)s')
# www.kindgirls.com
MAIN_URL = 'https://www.kindgirls.com/gallery.php?id={model_id}'

# set header
HEADER = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
    'Connection': 'close'
}

class KindGirls():
    async def parse_page(self,model_url):
        """
        This is a parse page program
        :param model_url: model url
        :return: call save_data() function to download photo file
        """
        # use PyQuery parse tool to parse model html file
        await asyncio.sleep(1)
        model_html = pq(model_url)

        # get model name
        model_name = model_html.find ('#up_izq h3').text()

        # use Regex Expression get model id
        pattern = re.compile(r'id=(\d+)')
        model_id = re.search(pattern, model_url).group(1)

        # iterable get model url
        number = 0
        for item in model_html ('.gal_list a').items():
            # use Regex Expression get model url
            model_urls = re.findall("""<a[^>]+href=["']([^'"<>]+)["'][^<>]+/?>""", str(item))
            for model_url in model_urls:
                
                # JPG file path
                number += 1
                photo_name = model_name + f'_{model_id}_' + str (number)

                # photo path
                model_photo_path = f'KindGirls/{model_name}/{model_name}_{model_id}/{photo_name}.jpg'

                # model photo path
                photo_dir = f'KindGirls/{model_name}/{model_name}_{model_id}'

                # judgement path
                if exists(model_photo_path):
                    # logging.info(f'{photo_name} is existed, skip download')
                    pass
                elif not exists(photo_dir):
                    makedirs (photo_dir)
                    logging.info(f"Create {model_name}_{model_id} Successfully!")
                elif not exists(model_photo_path) or getsize(model_photo_path) == 0:
                    logging.info (f"=======Asyncio Task : {photo_name}=======")
                    # call async_download() function
                    await self.async_download(model_url, photo_dir, photo_name)

    async def async_download(self, model_url, photo_dir, photo_name):
        """
        This is a download program
        :param photo_name: model photo name
        :param model_url: model url
        :param model_name: model name
        :param model_id: model id
        :param photo_dir: photo dir
        """
        # use aiohttp.ClientSession and aiofiles async download photo to local computer
        async with aiohttp.ClientSession(headers=HEADER) as session:
            async with session.get(model_url) as response:

                # use aiofiles library asyncio download photo
                async with aiofiles.open(f'{photo_dir}/{photo_name}.jpg', 'wb') as afp:
                    await afp.write(await response.content.read())
                    logging.info(f'Saving {photo_name}.jpg Successfully')

                    # close aiofiles async program
                    await afp.close()

    async def main(self,start_to_end):
        """
        This is a main program
        :return:
        """

        # timeout = aiohttp.ClientTimeout(total=100, connect=20,sock_connect=10,sock_read=10)
        async with aiohttp.ClientSession(headers=HEADER) as session:

            # start asyncio task
            tasks = [asyncio.ensure_future(self.parse_page(MAIN_URL.format(model_id=model_id)))
                        for model_id in range(start_to_end[0], start_to_end[1]+1)]

            # use asyncio.gather method
            responses = asyncio.gather(*tasks)
            await responses
            await session.close()

    def exception_handler(self):
        user_input = input ('Are you want continue run program[y]')
        if user_input == 'y' or user_input == 'Y':
            self.kind_girls_run ()
        else:
            quit()

    def input_handler(self):
        # model start download ID
        START_ID = int(input ('You have to input Start Number: '))

        # model end download ID
        END_ID = int(input ('You have to input End Number: '))

        # set tuple: start_to_end storge START_ID and END_ID
        start_to_end = (START_ID, END_ID)

        return start_to_end

    def kind_girls_run(self):
        """
        loop running program
        :return:
        """
        # call input function
        input_id = self.input_handler ()

        # set flag is True
        flag = True

        # use while statement
        while flag:
            try:
                # start time
                start_time = time.time ()

                loop = asyncio.get_event_loop ()
                loop.run_until_complete ((self.main(input_id)))

                # end time
                end_time = time.time ()

                # display program consumed time
                logging.info (f"Total Consumed Time : {round ((end_time - start_time) / 60)} Minus")

                # set flag is False, quit while statement
                flag = False

            # except aiohttp.ClientTimeout or aiohttp.ClientConnectorError or socket.timeout  as e:
            except Exception as e:
                # sleep 1 seconds
                logging.info ('=====================================================')
                # print(e)
                logging.error (f'---Occurred {e} Error, 5 seconds after try again--- ')
                # logging.info ('=====================================================')
                time.sleep(10)
                # self.exception_handler ()
                continue
            except KeyboardInterrupt:
                logging.info ('Download Program are exited')


if __name__ == "__main__":
    # call kind_girls_run() function
    # start running program
    kind_girls = KindGirls()
    kind_girls.kind_girls_run()



