import plistlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENTITLEMENTS = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "TreningsCoach.entitlements"
)
INFO_PLIST = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Info.plist"
)
PBXPROJ = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach.xcodeproj"
    / "project.pbxproj"
)


def test_entitlements_file_is_valid_plist_dict():
    with ENTITLEMENTS.open("rb") as f:
        parsed = plistlib.load(f)
    assert isinstance(parsed, dict)
    assert "com.apple.developer.healthkit" in parsed


def test_project_does_not_enable_entitlements_modification_override():
    text = PBXPROJ.read_text(encoding="utf-8")
    assert "CODE_SIGN_ALLOW_ENTITLEMENTS_MODIFICATION = YES;" not in text


def test_project_capabilities_match_entitlements_configuration():
    text = PBXPROJ.read_text(encoding="utf-8")
    assert "com.apple.HealthKit" in text

    with INFO_PLIST.open("rb") as f:
        info = plistlib.load(f)

    if bool(info.get("APPLE_SIGN_IN_ENABLED", False)):
        assert "com.apple.SignInWithApple" in text


def test_apple_signin_disabled_mode_has_no_apple_entitlement():
    with INFO_PLIST.open("rb") as f:
        info = plistlib.load(f)
    apple_signin_enabled = bool(info.get("APPLE_SIGN_IN_ENABLED", False))

    with ENTITLEMENTS.open("rb") as f:
        entitlements = plistlib.load(f)

    has_apple_signin_entitlement = "com.apple.developer.applesignin" in entitlements
    if not apple_signin_enabled:
        assert not has_apple_signin_entitlement
