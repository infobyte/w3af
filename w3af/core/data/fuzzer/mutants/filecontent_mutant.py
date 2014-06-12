"""
filecontent_mutant.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.core.data.fuzzer.mutants.mutant import Mutant
from w3af.core.data.dc.form import Form
from w3af.core.data.dc.utils.file_token import FileDataToken
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.dc.multipart_container import MultipartContainer


class FileContentMutant(PostDataMutant):
    """
    This class is a file content mutant, this means that the payload is sent
    in the content of a file which is uploaded over multipart/post
    """
    @staticmethod
    def get_mutant_type():
        return 'file content'

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        dc = self.get_dc()
        dc_short = dc.get_short_printable_repr()

        msg = '"%s", using HTTP method %s. The sent post-data was: "%s"' \
              " which modified the uploaded file content."

        return msg % (self.get_url(), self.get_method(), dc_short)

    @staticmethod
    def create_mutants(freq, payload_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not 'fuzz_form_files' in fuzzer_config:
            return []

        if not freq.get_file_vars():
            return []

        if not isinstance(freq.get_raw_data(), Form):
            return []

        form = freq.get_raw_data()
        multipart_container = OnlyTokenFilesMultipartContainer.from_form(form)
        freq.set_data(multipart_container)

        res = Mutant._create_mutants_worker(freq, FileContentMutant,
                                            payload_list,
                                            freq.get_file_vars(),
                                            append, fuzzer_config)
        return res


class OnlyTokenFilesMultipartContainer(MultipartContainer):
    """
    A MultipartContainer which only allows me to tokenize (and then modify) the
    parameters which are going to be later send as files by multipart/encoding.

    Also, when fuzzing I'll be creating my tokens using FileDataToken: a great
    way to abstract the fact that payloads are sent in the content of a file.
    """
    DATA_TOKEN_KLASS = FileDataToken

    def set_token(self, key_name, index_num):
        """
        Modified to pass the filename to the FileDataToken
        """
        for k, v in self.items():
            for idx, ele in enumerate(v):
                if not self.token_filter(k, idx, ele):
                    continue

                if key_name == k and idx == index_num:

                    if hasattr(ele, 'filename') and k in self.get_file_vars():
                        token = FileDataToken(k, ele, ele.filename)
                    else:
                        token = DataToken(k, ele)

                    self[k][idx] = token
                    self.token = token

                    return token