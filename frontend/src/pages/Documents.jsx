import React, { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Upload, FileText, Trash2, X, AlertCircle, CheckCircle, Info, ChevronRight, File, Sparkles } from 'lucide-react'
import client from '../api/client'
import { useWorkspace } from '../context/WorkspaceContext'
import { formatDistanceToNow } from 'date-fns'
import { motion, AnimatePresence } from 'framer-motion'

const Documents = () => {
  const { id } = useParams()
  const { refreshStats } = useWorkspace()
  
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [docDetail, setDocDetail] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  
  const fileInputRef = useRef(null)
  const pollingIntervalRef = useRef(null)

  const fetchDocs = async (showLoading = true) => {
    if (showLoading) setLoading(true)
    try {
      const response = await client.get(`/documents/${id}`)
      setDocuments(response.data)
      
      const hasProcessing = response.data.some(d => d.status === 'processing')
      if (hasProcessing) {
        startPolling()
      } else {
        stopPolling()
      }
    } catch (err) {
      console.error("Failed to load documents", err)
    } finally {
      if (showLoading) setLoading(false)
    }
  }

  const startPolling = () => {
    if (pollingIntervalRef.current) return
    pollingIntervalRef.current = setInterval(() => {
      fetchDocs(false)
      refreshStats()
    }, 2000)
  }

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
  }

  useEffect(() => {
    fetchDocs()
    return () => stopPolling()
  }, [id])

  const handleDocClick = async (doc) => {
    setSelectedDoc(doc)
    setDocDetail(null)
    setLoadingDetail(true)
    
    try {
      const response = await client.get(`/documents/${id}/${doc.id}`)
      setDocDetail(response.data)
    } catch (err) {
      console.error("Failed to load document details", err)
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return
    await uploadFile(selectedFile)
  }

  const uploadFile = async (fileObj) => {
    setUploading(true)
    setUploadError(null)

    const formData = new FormData()
    formData.append('file', fileObj)

    try {
      await client.post(`/documents/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      await fetchDocs(false)
      refreshStats()
    } catch (err) {
      console.error("Upload failed", err)
      setUploadError(err.response?.data?.detail || 'Failed to upload document.')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (docId) => {
    const confirmDelete = window.confirm(
      "Are you sure? Deleting this document will remove all indexed chunks from the workspace memory."
    )
    if (!confirmDelete) return

    try {
      await client.delete(`/documents/${id}/${docId}`)
      setSelectedDoc(null)
      setDocDetail(null)
      await fetchDocs(false)
      refreshStats()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete document.')
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) {
      await uploadFile(droppedFile)
    }
  }

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  return (
    <div className="absolute inset-0 flex relative bg-[#F8F8F6] text-[#18181B] h-full overflow-hidden select-none">
      {/* Left documents view */}
      <div className="flex-1 flex flex-col p-6 sm:p-8 overflow-y-auto">
        <div className="mb-6">
          <h2 className="font-display font-bold text-lg sm:text-xl text-[#18181B] tracking-tight">Documents Repository</h2>
          <p className="text-[#71717A] text-xs mt-0.5">Upload specs, technical documents, or research notes to index into the Workspace Brain.</p>
        </div>

        {/* Drag and Drop Zone */}
        <div 
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-[#E4E4E0] hover:border-[#18181B] bg-white hover:bg-[#F4F4F2]/50 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all mb-6 shadow-xs group"
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange}
            className="hidden" 
            accept=".pdf,.docx,.txt,.md"
          />
          <div className="w-11 h-11 rounded-xl bg-[#F4F4F2] group-hover:bg-[#E4E4E0] flex items-center justify-center text-[#18181B] transition-colors mb-3">
            <Upload className="w-5 h-5" />
          </div>
          <span className="text-sm font-bold text-[#18181B] transition-colors">
            {uploading ? 'Parsing and indexing document chunks...' : 'Click or drag file to index into workspace'}
          </span>
          <span className="text-[11px] text-[#71717A] mt-1 font-mono">
            Supported formats: PDF, DOCX, TXT, MD up to 20MB
          </span>
        </div>

        {uploadError && (
          <div className="mb-5 p-3 bg-[#FEF2F2] border border-[#FEE2E2] text-[#991B1B] text-xs rounded-xl flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Documents cards grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="h-20 bg-white border border-[#E4E4E0] rounded-xl animate-pulse shadow-xs"></div>
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div className="bg-white border border-[#E4E4E0] rounded-2xl p-10 flex flex-col items-center text-center shadow-xs max-w-md mx-auto my-6">
            <div className="w-10 h-10 rounded-xl bg-[#F4F4F2] flex items-center justify-center text-[#71717A] mb-3">
              <FileText className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold text-[#18181B]">No documents indexed yet</span>
            <p className="text-[11px] text-[#71717A] mt-1">Uploaded files are chunked, parsed, and made retrievable by all workspace agents.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {documents.map((doc) => {
              const isIndexed = doc.status === 'indexed'
              const isProcessing = doc.status === 'processing'
              const isFailed = doc.status === 'failed'
              const isSelected = selectedDoc?.id === doc.id
              
              return (
                <div 
                  key={doc.id}
                  onClick={() => handleDocClick(doc)}
                  className={`bg-white border rounded-xl p-4 flex items-center justify-between cursor-pointer transition-all hover:border-[#18181B] hover:shadow-xs ${
                    isSelected ? 'border-[#18181B] ring-2 ring-[#18181B]/10 shadow-xs' : 'border-[#E4E4E0]'
                  }`}
                >
                  <div className="flex items-center space-x-3.5 min-w-0">
                    <div className={`p-2.5 rounded-lg ${isSelected ? 'bg-[#18181B] text-white' : 'bg-[#F4F4F2] text-[#18181B]'}`}>
                      <FileText className="w-4 h-4 shrink-0" />
                    </div>
                    <div className="truncate min-w-0">
                      <h4 className="text-xs sm:text-sm font-bold text-[#18181B] truncate leading-snug">{doc.filename}</h4>
                      <div className="flex items-center space-x-2 text-[11px] text-[#71717A] mt-0.5">
                        <span>{formatSize(doc.size_bytes)}</span>
                        <span>·</span>
                        <span>{formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}</span>
                      </div>
                    </div>
                  </div>

                  {/* Status Indicator */}
                  <div className="ml-3 shrink-0">
                    {isProcessing && (
                      <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded text-[10px] font-medium bg-[#F4F4F2] text-[#71717A] border border-[#E4E4E0]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#71717A] animate-pulse"></span>
                        <span>indexing</span>
                      </span>
                    )}
                    {isIndexed && (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-[#F0FDF4] text-[#15803D] border border-[#DCFCE7]">
                        <CheckCircle className="w-3 h-3 text-[#15803D]" />
                        <span>{doc.chunk_count} chunks</span>
                      </span>
                    )}
                    {isFailed && (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-medium bg-[#FEF2F2] text-[#991B1B] border border-[#FEE2E2]" title={doc.error}>
                        <AlertCircle className="w-3 h-3 text-[#DC2626]" />
                        <span>failed</span>
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Right Details Sidebar Drawer */}
      <AnimatePresence>
        {selectedDoc && (
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 sm:static sm:w-[21rem] bg-white border-l border-[#E4E4E0] flex flex-col h-full overflow-y-auto shadow-lg z-10"
          >
            {/* Header */}
            <div className="p-4 border-b border-[#E4E4E0] flex items-center justify-between">
              <h3 className="font-display font-bold text-xs text-[#18181B] truncate pr-3">{selectedDoc.filename}</h3>
              <button 
                onClick={() => { setSelectedDoc(null); setDocDetail(null); }}
                className="text-[#71717A] hover:text-[#18181B] p-1 rounded-lg hover:bg-[#F4F4F2] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Details */}
            <div className="p-5 space-y-5 flex-grow">
              {loadingDetail ? (
                <div className="space-y-3">
                  <div className="h-4 w-24 bg-[#E4E4E0] rounded animate-pulse"></div>
                  <div className="h-28 bg-[#F4F4F2] rounded-xl animate-pulse"></div>
                </div>
              ) : docDetail ? (
                <div className="space-y-5">
                  {/* Meta details */}
                  <div className="space-y-2.5 font-sans text-xs bg-[#F8F8F6] p-3.5 rounded-xl border border-[#E4E4E0]">
                    <div className="flex justify-between text-[#52525B]">
                      <span className="text-[11px] font-semibold uppercase text-[#71717A]">Uploaded by</span>
                      <span className="font-semibold text-[#18181B]">{docDetail.uploader_name}</span>
                    </div>
                    <div className="flex justify-between text-[#52525B]">
                      <span className="text-[11px] font-semibold uppercase text-[#71717A]">Memory Chunks</span>
                      <span className="font-semibold text-[#18181B]">{docDetail.chunk_count}</span>
                    </div>
                    <div className="flex justify-between text-[#52525B]">
                      <span className="text-[11px] font-semibold uppercase text-[#71717A]">Pages Count</span>
                      <span className="font-semibold text-[#18181B]">{docDetail.page_count || 1}</span>
                    </div>
                    <div className="flex justify-between text-[#52525B]">
                      <span className="text-[11px] font-semibold uppercase text-[#71717A]">Status</span>
                      <span className={`font-semibold uppercase text-[10px] px-1.5 py-0.2 rounded ${
                        docDetail.status === 'indexed' ? 'bg-[#F0FDF4] text-[#15803D]' : 'bg-[#FEF2F2] text-[#991B1B]'
                      }`}>
                        {docDetail.status}
                      </span>
                    </div>
                  </div>

                  {/* AI Summary Section */}
                  <div className="space-y-2">
                    <div className="flex items-center space-x-1.5 text-xs text-[#18181B] font-semibold">
                      <FileText className="w-3.5 h-3.5 text-[#71717A]" />
                      <span>Workspace Brain Synthesis</span>
                    </div>
                    
                    <div className="text-xs leading-relaxed text-[#27272A] bg-[#F8F8F6] p-3.5 rounded-xl border border-[#E4E4E0] select-text font-sans">
                      {docDetail.summary ? (
                        docDetail.summary
                      ) : docDetail.status === 'indexed' ? (
                        <span className="italic text-[#71717A]">Document indexed into vector memory. Automatically cited during multi-agent discussions.</span>
                      ) : (
                        <span className="text-[#DC2626] font-medium">Document parsing encountered an issue.</span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-[#71717A] text-center pt-8">Could not load details.</div>
              )}
            </div>

            {/* Delete Button footer */}
            <div className="p-4 border-t border-[#E4E4E0] bg-[#F8F8F6] mt-auto">
              <button
                onClick={() => handleDelete(selectedDoc.id)}
                className="w-full bg-white hover:bg-[#FEF2F2] border border-[#E4E4E0] hover:border-[#FEE2E2] text-[#DC2626] py-2 rounded-xl font-semibold text-xs transition-all cursor-pointer flex items-center justify-center space-x-1.5 shadow-xs"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Document</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Documents
