import React, { useState, useRef } from 'react';

export interface RecordButtonProps {
  canvas: HTMLCanvasElement | null;
  videoElement: HTMLVideoElement | null;
  filename?: string;
  disabled?: boolean;
}

export const RecordButton: React.FC<RecordButtonProps> = ({
  canvas,
  videoElement,
  filename = 'video_export',
  disabled = false,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const handleStartRecording = () => {
    if (!canvas || !videoElement) {
      console.error('Canvas or video element not available');
      return;
    }

    try {
      // Get canvas stream
      const canvasStream = canvas.captureStream(30); // 30 FPS

      // Get audio from video element
      const audioContext = new AudioContext();
      const audioSource = audioContext.createMediaElementAudioSource(
        videoElement
      );
      const destinationNode = audioContext.createMediaStreamDestination();
      audioSource.connect(destinationNode);

      // Combine streams
      const audioTracks = destinationNode.stream.getAudioTracks();
      const combinedStream = new MediaStream([
        ...canvasStream.getTracks(),
        ...audioTracks,
      ]);

      // Create recorder
      const mediaRecorder = new MediaRecorder(combinedStream, {
        mimeType: 'video/webm',
      });

      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        downloadBlob(blob, `${filename}.webm`);
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const downloadBlob = (blob: Blob, name: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={
        isRecording ? handleStopRecording : handleStartRecording
      }
      disabled={disabled || !canvas || !videoElement}
      data-testid="record-button"
      className={isRecording ? 'recording' : ''}
    >
      {isRecording ? 'Stop Recording' : 'Start Recording'}
    </button>
  );
};
