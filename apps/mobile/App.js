import React, { useMemo, useState } from 'react';
import { SafeAreaView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

const API_BASE = 'http://192.168.1.5:8001';

export default function App() {
  const [transcript, setTranscript] = useState('3rd and 7, cover 3 nickel, ball on right hash');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [parsedEvent, setParsedEvent] = useState(null);
  const [recording, setRecording] = useState(null);

  const parsed = useMemo(() => {
    return {
      down: transcript.includes('4th') ? 4 : transcript.includes('3rd') ? 3 : transcript.includes('2nd') ? 2 : 1,
      distance: transcript.includes('and 7') ? 7 : 5,
      yard_line: 42,
      clock_seconds: 300,
      offense_personnel: '11',
      defense_shell: transcript.toLowerCase().includes('cover 2') ? 'Cover 2' : 'Cover 3',
      defense_front: transcript.toLowerCase().includes('nickel') ? 'Nickel' : 'Base',
      hash: transcript.toLowerCase().includes('left hash') ? 'left' : transcript.toLowerCase().includes('middle') ? 'middle' : 'right'
    };
  }, [transcript]);

  const requestSuggestions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/v1/voice/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript })
      });
      const data = await response.json();
      setTranscript(data.transcript ?? transcript);
      setParsedEvent(data.parsed_event ?? parsed);
      setSuggestions(data.recommendations ?? []);
    } catch {
      setParsedEvent(parsed);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (permission.status !== 'granted') {
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true
      });

      const { recording: nextRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      setRecording(nextRecording);
    } catch {
      setRecording(null);
    }
  };

  const stopRecordingAndAnalyze = async () => {
    if (!recording) {
      return;
    }

    setLoading(true);
    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);
      if (!uri) {
        return;
      }

      const audioBase64 = await FileSystem.readAsStringAsync(uri, {
        encoding: FileSystem.EncodingType.Base64
      });

      const response = await fetch(`${API_BASE}/v1/voice/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          audio_base64: audioBase64,
          mime_type: 'audio/m4a'
        })
      });
      const data = await response.json();
      setTranscript(data.transcript ?? transcript);
      setParsedEvent(data.parsed_event ?? parsed);
      setSuggestions(data.recommendations ?? []);
    } catch {
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="auto" />
      <Text style={styles.title}>Madden OC Voice Assistant</Text>
      <Text style={styles.subtitle}>Speak the situation like a coordinator, then get top plays.</Text>

      <TextInput value={transcript} onChangeText={setTranscript} style={styles.input} multiline />

      <View style={styles.voiceRow}>
        <TouchableOpacity style={styles.secondaryButton} onPress={startRecording}>
          <Text style={styles.secondaryButtonText}>{recording ? 'Recording...' : 'Start Voice'}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.secondaryButton} onPress={stopRecordingAndAnalyze}>
          <Text style={styles.secondaryButtonText}>Stop + Analyze</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.button} onPress={requestSuggestions}>
        <Text style={styles.buttonText}>{loading ? 'Analyzing...' : 'Analyze Situation'}</Text>
      </TouchableOpacity>

      {parsedEvent ? (
        <View style={styles.parsedCard}>
          <Text style={styles.meta}>Parsed: {parsedEvent.down}&{parsedEvent.distance}, {parsedEvent.defense_shell}, {parsedEvent.defense_front}</Text>
        </View>
      ) : null}

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Top Suggestions</Text>
        {suggestions.map((s, index) => (
          <View key={`${s.play_name}-${index}`} style={styles.card}>
            <Text style={styles.play}>{index + 1}. {s.play_name} ({Math.round(s.confidence * 100)}%)</Text>
            <Text style={styles.meta}>{s.formation} • {s.concept}</Text>
            <Text style={styles.reason}>{s.rationale}</Text>
          </View>
        ))}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', padding: 16 },
  title: { fontSize: 24, fontWeight: '700', marginBottom: 4 },
  subtitle: { fontSize: 14, color: '#555', marginBottom: 12 },
  input: {
    minHeight: 100,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 10,
    textAlignVertical: 'top',
    marginBottom: 12
  },
  voiceRow: { flexDirection: 'row', gap: 8, marginBottom: 10 },
  secondaryButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#111827',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center'
  },
  secondaryButtonText: { color: '#111827', fontWeight: '600' },
  button: {
    backgroundColor: '#111827',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 16
  },
  buttonText: { color: '#fff', fontWeight: '600' },
  parsedCard: { borderWidth: 1, borderColor: '#eee', borderRadius: 8, padding: 10, marginBottom: 10 },
  panel: { flex: 1 },
  panelTitle: { fontSize: 18, fontWeight: '600', marginBottom: 8 },
  card: { borderWidth: 1, borderColor: '#eee', borderRadius: 8, padding: 10, marginBottom: 8 },
  play: { fontWeight: '600' },
  meta: { color: '#666', marginTop: 2 },
  reason: { marginTop: 4 }
});
