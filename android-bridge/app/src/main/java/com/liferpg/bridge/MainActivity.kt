package com.liferpg.bridge

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.health.connect.client.PermissionController
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

/**
 * Minimal Android companion bridge activity for LIFE RPG.
 * Allows heroes to connect Android Health Connect activity directly
 * to their real-world RPG campaign quests.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var healthConnectManager: HealthConnectManager
    private lateinit var serverUrlInput: EditText
    private lateinit var tokenInput: EditText
    private lateinit var statusText: TextView
    private lateinit var grantBtn: Button
    private lateinit var syncBtn: Button

    // Health Connect Permission Launcher Contract
    private val requestPermissionLauncher = registerForActivityResult(
        PermissionController.createRequestPermissionResultContract()
    ) { grantedPermissions ->
        if (grantedPermissions.containsAll(healthConnectManager.requiredPermissions)) {
            statusText.text = "Status: All Health Connect permissions granted!"
            Toast.makeText(this, "Health Connect permissions granted", Toast.LENGTH_SHORT).show()
        } else {
            statusText.text = "Status: Partial or no permissions granted."
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        healthConnectManager = HealthConnectManager(this)

        // Simple programmatic layout
        val layout = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(48, 64, 48, 64)
        }

        val title = TextView(this).apply {
            text = "LIFE RPG — Health Connect Bridge"
            textSize = 20f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setPadding(0, 0, 0, 24)
        }
        layout.addView(title)

        val serverLabel = TextView(this).apply { text = "LIFE RPG Server URL:" }
        layout.addView(serverLabel)
        serverUrlInput = EditText(this).apply {
            setText("http://10.0.2.2:8000") // Default for Android Emulator
            hint = "http://192.168.1.10:8000 or production URL"
        }
        layout.addView(serverUrlInput)

        val tokenLabel = TextView(this).apply {
            text = "Pairing Token (from LIFE RPG Settings / Integrations):"
            setPadding(0, 20, 0, 0)
        }
        layout.addView(tokenLabel)
        tokenInput = EditText(this).apply {
            hint = "Paste pairing token here"
        }
        layout.addView(tokenInput)

        grantBtn = Button(this).apply {
            text = "1. Request Health Connect Permissions"
            setOnClickListener { requestPermissions() }
        }
        layout.addView(grantBtn)

        syncBtn = Button(this).apply {
            text = "2. Sync Health Activity to LIFE RPG"
            setOnClickListener { performSync() }
        }
        layout.addView(syncBtn)

        statusText = TextView(this).apply {
            text = if (healthConnectManager.isHealthConnectAvailable()) {
                "Status: Health Connect is available on this device."
            } else {
                "Status: Health Connect is not installed or unavailable."
            }
            setPadding(0, 32, 0, 0)
        }
        layout.addView(statusText)

        setContentView(layout)
    }

    private fun requestPermissions() {
        if (!healthConnectManager.isHealthConnectAvailable()) {
            Toast.makeText(this, "Health Connect is not available on this device.", Toast.LENGTH_LONG).show()
            return
        }
        requestPermissionLauncher.launch(healthConnectManager.requiredPermissions)
    }

    private fun performSync() {
        val serverUrl = serverUrlInput.text.toString().trim()
        val token = tokenInput.text.toString().trim()

        if (token.isEmpty()) {
            Toast.makeText(this, "Please enter your LIFE RPG pairing token.", Toast.LENGTH_SHORT).show()
            return
        }

        statusText.text = "Status: Reading Health Connect activity..."
        lifecycleScope.launch {
            try {
                val batch = healthConnectManager.readActivityData(lookbackHours = 48)
                statusText.text = "Status: Sending ${batch.sessions.size} sessions and ${batch.dailySteps} steps to server..."

                val client = BridgeSyncClient(serverUrl, token)
                val result = client.syncBatch(batch)

                result.onSuccess { responseJson ->
                    statusText.text = "Status: Sync Success!\n$responseJson"
                    Toast.makeText(this@MainActivity, "Sync successful!", Toast.LENGTH_SHORT).show()
                }.onFailure { err ->
                    statusText.text = "Status: Sync Error: ${err.message}"
                }
            } catch (e: Exception) {
                statusText.text = "Status: Unexpected error: ${e.message}"
            }
        }
    }
}
