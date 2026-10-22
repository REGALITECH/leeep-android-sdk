package jp.leeep.releasesmoke

import android.app.Activity
import android.os.Bundle
import jp.leeep.AndroidSDK.Leeep
import jp.leeep.AndroidSDK.makeLeeepTagView

// Reaches the SDK the way a customer app does so R8 keeps and checks those code paths.
// Uses only APIs available since 0.9.1, so older tags can still be validated when backfilling releases.
class SmokeActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Leeep.setUserId(null)
        setContentView(makeLeeepTagView(this, "release-smoke"))
    }
}
