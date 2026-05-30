"""Offline tests for parsing live remailer stats."""
from remailers.network import Remailer, parse_stats

# a trimmed real Frelled/echolot Cypherpunk stats post
SAMPLE = """\
Frelled Cypherpunk Stats - 2026-05-30

Stats-Version: 2.0
Cypherpunk   Latent-Hist   Latent  Uptime-Hist   Uptime  Options
------------------------------------------------------------------------
frell        110112110111    :36   ++++++++++++  100.0%   PR GO ATLE IN9
yeahno       211232432233   1:25   ++++++++++++  100.0%  DPR GO ATLE IN
dizum        329A7764B?12   3:51   +++++++++?++  100.0%   PR GO ATLEUIN0


Remailer-Capabilities:

$remailer{"dizum"} = "<remailer@dizum.com> cpunk max mix pgp pgponly repgp remix latent hash cut test ek ekx esub inflt50 rhop5 reord post klen64";
$remailer{"frell"} = "<godot@remailer.frell.eu.org> cpunk max mix pgp pgponly repgp remix latent hash cut test ekx inflt50 rhop5 reord post klen1024";
$remailer{"yeahno"} = "<mix@yeahno.net> cpunk max mix middle pgp pgponly repgp remix esubbf hsub latent hash cut test ekx inflt50 rhop5 reord post";
"""


def test_parse_stats_finds_all_remailers():
    remailers = parse_stats(SAMPLE)
    names = {r.name for r in remailers}
    assert names == {"dizum", "frell", "yeahno"}
    assert all(isinstance(r, Remailer) for r in remailers)


def test_parse_stats_addresses_and_caps():
    by_name = {r.name: r for r in parse_stats(SAMPLE)}
    dizum = by_name["dizum"]
    assert dizum.address == "remailer@dizum.com"
    assert dizum.email == "remailer@dizum.com"
    assert dizum.supports("cpunk")
    assert dizum.accepts_pgp
    assert dizum.can_post
    assert not dizum.supports("middle")
    assert by_name["yeahno"].supports("middle")


def test_parse_stats_latency_and_uptime():
    by_name = {r.name: r for r in parse_stats(SAMPLE)}
    assert by_name["frell"].latency == ":36"
    assert by_name["frell"].uptime == "100.0%"
    assert by_name["dizum"].latency == "3:51"


def test_remailer_is_frozen():
    r = Remailer("x", "x@y")
    try:
        r.name = "z"  # type: ignore[misc]
    except Exception as exc:
        assert exc.__class__.__name__ == "FrozenInstanceError"
    else:
        raise AssertionError("Remailer should be immutable")
