"use client";

import { useState } from "react";
import Cropper, { Area, Point } from "react-easy-crop";
import { ApiError, Media, UploadProgress, api } from "@/lib/api";
import UploadProgressBar from "@/components/UploadProgressBar";
import { btnPrimary, btnSecondary, btnSmall } from "@/lib/ui";
import { getCroppedImageBlob } from "@/lib/cropImage";

export default function HeadshotUploader({
  token,
  hasExisting,
  onUploaded,
}: {
  token: string;
  hasExisting: boolean;
  onUploaded: (m: Media) => void;
}) {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [crop, setCrop] = useState<Point>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState<UploadProgress | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setError(null);
    setCrop({ x: 0, y: 0 });
    setZoom(1);
    setCroppedAreaPixels(null);
    setImageSrc(URL.createObjectURL(file));
  }

  function handleCancel() {
    if (imageSrc) URL.revokeObjectURL(imageSrc);
    setImageSrc(null);
  }

  async function handleSave() {
    if (!imageSrc || !croppedAreaPixels) return;
    setSubmitting(true);
    setError(null);
    setProgress(null);
    try {
      const blob = await getCroppedImageBlob(imageSrc, croppedAreaPixels);
      const media = await api.uploadMyCoverPhoto(blob, token, setProgress);
      onUploaded(media);
      URL.revokeObjectURL(imageSrc);
      setImageSrc(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not upload your photo.");
    } finally {
      setSubmitting(false);
      setProgress(null);
    }
  }

  return (
    <>
      <label className={`cursor-pointer ${btnSmall}`}>
        {hasExisting ? "Change photo" : "Add photo"}
        <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
      </label>

      {imageSrc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="flex w-full max-w-md flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-6 shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
            <h3 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">Position your photo</h3>
            <p className="text-sm text-zinc-500">Drag to reposition, scroll or pinch to zoom.</p>
            <div className="relative h-80 w-full overflow-hidden rounded-lg bg-zinc-100 dark:bg-zinc-800">
              <Cropper
                image={imageSrc}
                crop={crop}
                zoom={zoom}
                aspect={1}
                onCropChange={setCrop}
                onZoomChange={setZoom}
                onCropComplete={(_area, areaPixels) => setCroppedAreaPixels(areaPixels)}
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex justify-end gap-2">
              <button type="button" onClick={handleCancel} disabled={submitting} className={btnSecondary}>
                Cancel
              </button>
              <button type="button" onClick={handleSave} disabled={submitting} className={btnPrimary}>
                {submitting ? "Uploading…" : "Save photo"}
              </button>
            </div>
            <UploadProgressBar progress={progress} />
          </div>
        </div>
      )}
    </>
  );
}
