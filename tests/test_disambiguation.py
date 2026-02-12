class TestKDisambiguation:
    def test_ke_postposition_la(self, normalizer):
        assert normalizer("k'a la") == "kɛ a la"

    def test_ke_postposition_ye(self, normalizer):
        assert normalizer("k'a ye") == "kɛ a ye"

    def test_ke_postposition_fe(self, normalizer):
        assert normalizer("k'a fɛ") == "kɛ a fɛ"

    def test_ke_in_sentence(self, normalizer):
        assert normalizer("E de ye nin k'a la wa") == "e de ye nin kɛ a la wa"

    def test_ke_benefactive_ma_noun_ye(self, normalizer):
        """Test benefactive: k' + ma + NOUN + ye => kɛ"""
        assert normalizer("k'a ma hɛrɛ ye") == "kɛ a ma hɛrɛ ye"
        assert normalizer("k'a ma tasuma ye") == "kɛ a ma tasuma ye"
        assert normalizer("k'a ma yɛrɛ ye") == "kɛ a ma yɛrɛ ye"
        assert normalizer("k'u ma yɛrɛ ye") == "kɛ u ma yɛrɛ ye"

    def test_ke_benefactive_full_sentence(self, normalizer):
        assert normalizer("Nin ka k'a ma tasuma ye") == "nin ka kɛ a ma tasuma ye"

    def test_ka_verb_ta(self, normalizer):
        assert normalizer("k'a ta") == "ka a ta"

    def test_ka_verb_fo(self, normalizer):
        assert normalizer("k'a fɔ") == "ka a fɔ"

    def test_ka_verb_di(self, normalizer):
        assert normalizer("k'a di") == "ka a di"

    def test_ka_verb_dun(self, normalizer):
        assert normalizer("k'a dun") == "ka a dun"

    def test_ka_in_sentence(self, normalizer):
        assert normalizer("nin ta k'a di Musa ma") == "nin ta ka a di musa ma"

    def test_ka_no_lookahead(self, normalizer):
        assert normalizer("k'a") == "ka a"

    def test_ko_marker_kana(self, normalizer):
        assert normalizer("k'an kana") == "ko an kana"

    def test_ko_marker_ka(self, normalizer):
        assert normalizer("k'an ka ta so") == "ko an ka ta so"

    def test_ko_marker_u_ka(self, normalizer):
        assert normalizer("k'u ka na") == "ko u ka na"

    def test_ko_marker_anw_kana(self, normalizer):
        assert normalizer("k'anw kana") == "ko anw kana"

    def test_ko_ma_reported_speech(self, normalizer):
        """Test reported speech: k' + ma + CLAUSE_MARKER => ko"""
        assert normalizer("k'anw ma ko Ameriki kadi") == "ko anw ma ko ameriki kadi"

    def test_ko_emphatic_yere(self, normalizer):
        result = normalizer("k'ale yɛrɛ de y'a k'a la")
        assert "ko ale" in result
        assert "kɛ a la" in result

    def test_ko_full_sentence(self, normalizer):
        result = normalizer("A kɛ Ala kama i ka taa fɔ k'u ka na")
        assert "ko u ka na" in result

    def test_multiple_k_contractions(self, normalizer):
        result = normalizer("k'ale yɛrɛ de y'a k'a la")
        assert "ko ale" in result
        assert "kɛ a la" in result


class TestNDisambiguation:
    def test_ni_default(self, normalizer):
        """n' defaults to ni when not followed by pronoun + ma"""
        assert normalizer("n'a ta") == "ni a ta"
        assert normalizer("n'i bɛ") == "ni i bɛ"

    def test_na_with_ma(self, normalizer):
        """n' + pronoun + ma => na (come to)"""
        assert normalizer("n'a ma") == "na a ma"
        assert normalizer("n'i ma") == "na i ma"
        assert normalizer("n'u ma") == "na u ma"


class TestBackwardContext:
    """Tests for bidirectional context disambiguation (NEW)."""

    def test_speech_verb_fo_with_emphatic_ale(self, normalizer):
        """Backward speech verb fɔ + emphatic ale → ko (reported speech)."""
        result = normalizer("A y'a fɔ k'ale filɛ")
        assert "ko ale" in result

    def test_speech_verb_fo_with_emphatic_olu(self, normalizer):
        """Backward speech verb fɔ + emphatic olu → ko."""
        result = normalizer("A y'a fɔ k'olu taa")
        assert "ko olu" in result

    def test_speech_verb_fo_with_emphatic_anw(self, normalizer):
        """Backward speech verb fɔ + emphatic anw → ko."""
        result = normalizer("A y'a fɔ k'anw taa")
        assert "ko anw" in result

    def test_speech_verb_jaabi_with_emphatic(self, normalizer):
        """Backward speech verb jaabi + emphatic pronoun → ko."""
        result = normalizer("A y'a jaabi k'ale bɔra")
        assert "ko ale" in result

    def test_speech_verb_nininka_with_emphatic(self, normalizer):
        """Backward speech verb ɲininka + emphatic pronoun → ko."""
        result = normalizer("A y'a ɲininka k'ale bɛna taa")
        assert "ko ale" in result

    def test_speech_verb_with_simple_pronoun_stays_ka(self, normalizer):
        """Speech verb + simple pronoun a → still ka (infinitive instruction)."""
        assert normalizer("A y'a fɔ k'a ta") == "a ye a fɔ ka a ta"

    def test_speech_verb_with_simple_pronoun_i_stays_ka(self, normalizer):
        """Speech verb + simple pronoun i → still ka."""
        result = normalizer("A y'a fɔ k'i dun")
        assert "ka i" in result

    def test_no_speech_verb_emphatic_stays_ka(self, normalizer):
        """Without speech verb, emphatic pronoun still defaults to ka."""
        assert normalizer("k'ale ta a la") == "ka ale ta a la"

    def test_no_speech_verb_emphatic_default(self, normalizer):
        """No backward speech context → default ka for emphatic."""
        assert normalizer("k'olu filɛ") == "ka olu filɛ"

    def test_forward_rules_override_backward(self, normalizer):
        """Forward postposition still takes priority over backward context."""
        result = normalizer("A y'a fɔ k'a la")
        assert "kɛ a la" in result

    def test_forward_clause_marker_with_backward(self, normalizer):
        """Forward clause marker still gives ko (backward context is redundant)."""
        result = normalizer("A y'a fɔ k'an ka taa")
        assert "ko an ka taa" in result

    def test_speech_verb_perfective_fora(self, normalizer):
        """Perfective form fɔra also triggers backward context."""
        result = normalizer("A fɔra k'ale taa")
        assert "ko ale" in result


class TestNewPostpositions:
    """Tests for newly added postpositions (kan, na)."""

    def test_ke_postposition_kan(self, normalizer):
        """k' + pronoun + kan → kɛ (on top of / about)."""
        assert normalizer("k'a kan") == "kɛ a kan"

    def test_ke_postposition_na(self, normalizer):
        """k' + pronoun + na → kɛ (in/at, dialectal variant of la)."""
        assert normalizer("k'a na") == "kɛ a na"

    def test_ke_kan_in_sentence(self, normalizer):
        """kan postposition in a full sentence."""
        assert normalizer("A ye nin k'a kan") == "a ye nin kɛ a kan"

    def test_ke_na_in_sentence(self, normalizer):
        """na postposition in a full sentence."""
        result = normalizer("I ka k'a na sigida la")
        assert "kɛ a na" in result


class TestTAMMarkersFromDaba:
    """Tests for TAM (Tense-Aspect-Mood) markers informed by Daba's pm category."""

    def test_ko_with_bena_future(self, normalizer):
        """k' + pronoun + bɛna (future) → ko (full clause with TAM)."""
        result = normalizer("k'a bɛna taa")
        assert "ko a bɛna" in result

    def test_ko_with_tena_negative_future(self, normalizer):
        """k' + pronoun + tɛna (negative future) → ko."""
        result = normalizer("k'a tɛna na")
        assert "ko a tɛna" in result

    def test_ko_with_tun_past(self, normalizer):
        """k' + pronoun + tun (past) → ko (past clause)."""
        result = normalizer("k'a tun bɛ yen")
        assert "ko a tun" in result

    def test_ko_with_be_tam(self, normalizer):
        """k' + pronoun + bɛ (imperfective) → ko."""
        result = normalizer("k'a bɛ na")
        assert "ko a bɛ" in result

    def test_ko_with_te_negative(self, normalizer):
        """k' + pronoun + tɛ (negative imperfective) → ko."""
        result = normalizer("k'a tɛ se")
        assert "ko a tɛ" in result

    def test_ko_with_emphatic_particle_de(self, normalizer):
        """k' + pronoun + de (emphatic particle) → ko."""
        result = normalizer("k'ale de y'a kɛ")
        assert "ko ale de" in result

    def test_ko_with_emphatic_particle_de_simple(self, normalizer):
        """k' + pronoun + dɛ (emphatic particle variant) → ko."""
        result = normalizer("k'a dɛ")
        assert "ko a dɛ" in result

    def test_ko_with_yere_reflexive(self, normalizer):
        """k' + pronoun + yɛrɛ (self/reflexive emphatic) → ko."""
        result = normalizer("k'a yɛrɛ ye a kɛ")
        assert "ko a yɛrɛ" in result

    def test_ko_with_mana_conditional(self, normalizer):
        """k' + pronoun + mana (conditional marker) → ko."""
        result = normalizer("k'a mana taa")
        assert "ko a mana" in result


class TestComplexDisambiguation:
    def test_k_followed_by_k_contraction(self, normalizer):
        """k'o k'a la => ka o kɛ a la"""
        assert normalizer("Ka na son k'o k'a la") == "ka na son ka o kɛ a la"

    def test_k_with_ma_ko_reported_speech(self, normalizer):
        """Ne k'a ma ko ayi => Ne ko a ma ko ayi"""
        assert normalizer("Ne k'a ma ko ayi") == "ne ko a ma ko ayi"

    def test_k_ale_with_expanded_contraction_lookahead(self, normalizer):
        """K'ale t'a fɛ k'a kɛ => Ko ale tɛ a fɛ ka a kɛ"""
        assert normalizer("K'ale t'a fɛ k'a kɛ") == "ko ale tɛ a fɛ ka a kɛ"

    def test_n_contraction_na_come_to(self, normalizer):
        """N'ala son n'a ma => Ni ala son na a ma"""
        assert normalizer("N'ala son n'a ma") == "ni ala son na a ma"

    def test_k_i_pronoun_with_clause_marker(self, normalizer):
        """K'i k'i janto i yɛrɛ la => Ko i ka i janto i yɛrɛ la"""
        assert normalizer("K'i k'i janto i yɛrɛ la") == "ko i ka i janto i yɛrɛ la"

    def test_k_o_pronoun_basic(self, normalizer):
        """Test k'o with various following words"""
        assert normalizer("k'o la") == "kɛ o la"
        assert normalizer("k'o ta") == "ka o ta"

    def test_k_i_pronoun_basic(self, normalizer):
        """Test k'i with various following words"""
        assert normalizer("k'i la") == "kɛ i la"
        assert normalizer("k'i ta") == "ka i ta"
        assert normalizer("k'i ka taa") == "ko i ka taa"

    def test_complex_sentence_multiple_contractions(self, normalizer):
        """Test sentence with multiple different contractions"""
        result = normalizer("N'a ma k'u ka a ta")
        assert "na a ma" in result
        assert "ko u ka" in result

    def test_backward_and_forward_combined(self, normalizer):
        """Speech verb in backward + clause marker in forward → ko (both agree)."""
        result = normalizer("Musa y'a fɔ k'an ka taa")
        assert "ko an ka taa" in result

    def test_multiple_contractions_with_speech_verb(self, normalizer):
        """Full sentence: He told him that HE himself did it."""
        result = normalizer("A y'a fɔ k'ale yɛrɛ de y'a kɛ")
        assert "ko ale" in result
