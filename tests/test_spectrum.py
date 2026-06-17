from app.spectrum import calculate_spectrum


def test_calculate_spectrum_returns_percentages_and_dominant():
    result = calculate_spectrum(["A", "B", "C", "D", "E", "A", "B", "C", "D", "E"])

    assert sum(result["percentages"].values()) == 100
    assert result["dominant"] == "Mixto"
    assert "summary" in result
    assert "share_text" in result


def test_calculate_spectrum_returns_single_dominant_when_clear():
    result = calculate_spectrum(["A", "A", "A", "A", "A", "A", "A", "A", "A", "A"])

    assert result["dominant"] == "Ultraderecha"
    assert "orden" in result["summary"].lower()
