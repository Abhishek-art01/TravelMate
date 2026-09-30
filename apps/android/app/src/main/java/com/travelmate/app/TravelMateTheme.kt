package com.travelmate.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val TravelMateColors = darkColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFF38BDF8),
    secondary = androidx.compose.ui.graphics.Color(0xFF34D399),
    background = androidx.compose.ui.graphics.Color(0xFF08131D),
    surface = androidx.compose.ui.graphics.Color(0xFF0F172A),
)

@Composable
fun TravelMateTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = TravelMateColors,
        content = content,
    )
}
