from replacer import CaseAwareReplacer
import unittest

class TestCafeAwareReplacer(unittest.TestCase):
    def test_simple_same_case_replacements(self):
        r = CaseAwareReplacer("old_string", "new_string")
        self.assertEqual(r.replace("this is a old_string"), "this is a new_string")

        r = CaseAwareReplacer("old-string", "new-string")
        self.assertEqual(r.replace("this is a old-string"), "this is a new-string")

        r = CaseAwareReplacer("oldString", "newString")
        self.assertEqual(r.replace("this is a oldString"), "this is a newString")

    def test_case_matching_logic(self):
        r = CaseAwareReplacer("old", "nouveAU")

        self.assertEqual(r.replace("old"), "nouveAU")
        self.assertEqual(r.replace("OLD"), "NOUVEAU")
        self.assertEqual(r.replace("Old"), "NouveAU")

    def test_multi_part_case_matching(self):
        r = CaseAwareReplacer("user/name", "account/id")

        self.assertEqual(r.replace("user_name"), "account_id")
        self.assertEqual(r.replace("USER_NAME"), "ACCOUNT_ID")
        self.assertEqual(r.replace("UserName"), "AccountId")
        self.assertEqual(r.replace("user_NAME"), "account_ID")
        self.assertEqual(r.replace("USER-name"), "ACCOUNT-id")
        self.assertEqual(r.replace("USER-_-name"), "ACCOUNT-_-id")

    def test_replacement_expansion(self):
        r_multi = CaseAwareReplacer("the/url/is", "the/uniform/resource/is")

        base_str = "the_Url-IS_here"
        expected = "the_Uniform-RESOURCE-IS_here"
        self.assertEqual(r_multi.replace(base_str), expected)

    def test_replacement_contraction(self):
        r = CaseAwareReplacer("hyper/text/markup/language", "html")

        self.assertEqual(r.replace("hyperTextMarkupLanguage"), "html")
        self.assertEqual(r.replace("HyperTextMarkupLANGUAGE"), "Html")
        self.assertEqual(r.replace("hyper__text_markup_Language"), "html")
        self.assertEqual(r.replace("HYPER--TEXT-MARKUP-LANGUAGE"), "HTML")

    def test_no_match(self):
        r = CaseAwareReplacer("nonexistent", "string")

        base_str = "this is a string that will not be changed"
        self.assertEqual(r.replace(base_str), base_str)

    def test_multiple_matches(self):
        r = CaseAwareReplacer("cat", "dog")

        base_str = "The black cat and the white cat"
        expected = "The black dog and the white dog"
        self.assertEqual(r.replace(base_str), expected)

        base_str_cased = "A CAT, a Cat, and a cat."
        expected_cased = "A DOG, a Dog, and a dog."
        self.assertEqual(r.replace(base_str_cased), expected_cased)

    def test_mixed_separators_and_numbers(self):
        r = CaseAwareReplacer("ipv4/address", "internet/protocol/v4/addr")

        base_str = "The ipv4-address is 127.0.0.1"
        expected = "The internet-protocol-v4-addr is 127.0.0.1"
        self.assertEqual(r.replace(base_str), expected)

        base_str_camel = "The Ipv4Address is 127.0.0.1"
        expected_camel = "The InternetProtocolV4Addr is 127.0.0.1"
        self.assertEqual(r.replace(base_str_camel), expected_camel)

    def test_expansion_from_single_word(self):
        r = CaseAwareReplacer("id", "identification/number")

        self.assertEqual(r.replace("user_id"), "user_identificationnumber")
        self.assertEqual(r.replace("userId"), "userIdentificationNumber")

if __name__ == '__main__':
    unittest.main()