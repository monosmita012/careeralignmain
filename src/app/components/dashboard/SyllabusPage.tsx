import { useState } from 'react';
import { Upload, FileText, CheckCircle, Eye, X, File as FileIcon, Trash2, Image, FileType } from 'lucide-react';
import { Button } from '../ui/button';
import { useUser } from '../../context/UserContext';
import { toast } from 'sonner';

export default function SyllabusPage() {
  const { userData, addSyllabusFile, removeSyllabusFile, uploadSyllabus } = useUser();
  const [isDragging, setIsDragging] = useState(false);
  const [viewingFile, setViewingFile] = useState<{fileName: string, content: string, type: string} | null>(null);

  const getFileType = (file: File): 'pdf' | 'image' | 'text' => {
    if (file.type.includes('pdf')) return 'pdf';
    if (file.type.includes('image')) return 'image';
    return 'text';
  };

  const handleFileUpload = (files: FileList | File[]) => {
    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        const fileType = getFileType(file);
        
        addSyllabusFile({
          fileName: file.name,
          content,
          type: fileType,
        });
        
        // Also update legacy single syllabus for compatibility
        if (userData.syllabusFiles.length === 0) {
          uploadSyllabus(file.name, content);
        }
        
        toast.success(`${file.name} uploaded successfully!`);
      };
      reader.readAsDataURL(file);
    });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files);
    }
    // Reset input so same file can be re-uploaded
    e.target.value = '';
  };

  const handleDelete = (id: string, fileName: string) => {
    removeSyllabusFile(id);
    toast.success(`${fileName} removed`);
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf': return <FileText className="w-8 h-8 text-red-500" />;
      case 'image': return <Image className="w-8 h-8 text-blue-500" />;
      default: return <FileType className="w-8 h-8 text-gray-500" />;
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">📚 Upload Syllabus</h1>
        <p className="text-gray-600 dark:text-gray-300">
          Upload multiple PDFs and images of your course syllabus to receive personalized learning recommendations
        </p>
      </div>

      {/* Upload Area */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 border-2 border-dashed transition-all duration-300 mb-6 ${
          isDragging
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
        }`}
      >
        <div className="text-center">
          <div className="p-4 bg-blue-100 dark:bg-blue-900 rounded-full w-fit mx-auto mb-4">
            <Upload className="w-10 h-10 text-blue-600 dark:text-blue-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
            Drag & Drop Files Here
          </h3>
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            or click to browse • supports PDFs and Images
          </p>
          <Button
            onClick={() => document.getElementById('multi-syllabus-upload')?.click()}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Upload className="w-4 h-4 mr-2" />
            Choose Files
          </Button>
          <input
            id="multi-syllabus-upload"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.gif,.webp,.txt,.doc,.docx"
            onChange={handleFileInput}
            multiple
            className="hidden"
          />
        </div>
      </div>

      {/* Uploaded Files Grid */}
      {userData.syllabusFiles.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              Uploaded Files ({userData.syllabusFiles.length})
            </h2>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {userData.syllabusFiles.map((file) => (
              <div
                key={file.id}
                className="relative bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600 hover:shadow-md transition-all group"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 p-2 bg-white dark:bg-gray-800 rounded-lg">
                    {getFileIcon(file.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white truncate" title={file.fileName}>
                      {file.fileName}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase mt-1">
                      {file.type}
                    </p>
                  </div>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2 mt-3">
                  <Button
                    onClick={() => setViewingFile({ fileName: file.fileName, content: file.content, type: file.type })}
                    size="sm"
                    className="flex-1 bg-purple-600 hover:bg-purple-700 text-white text-xs"
                  >
                    <Eye className="w-3 h-3 mr-1" />
                    View
                  </Button>
                  <Button
                    onClick={() => handleDelete(file.id, file.fileName)}
                    size="sm"
                    variant="destructive"
                    className="text-xs"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View Modal */}
      {viewingFile && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">{viewingFile.fileName}</h3>
              </div>
              <button
                onClick={() => setViewingFile(null)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              {viewingFile.content.startsWith('data:application/pdf') ? (
                <iframe
                  src={viewingFile.content}
                  className="w-full h-[70vh] rounded-lg border border-gray-200 dark:border-gray-700"
                  title="Document Preview"
                />
              ) : viewingFile.content.startsWith('data:image/') ? (
                <img
                  src={viewingFile.content}
                  alt="Syllabus"
                  className="max-w-full mx-auto rounded-lg"
                />
              ) : (
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 max-h-[70vh] overflow-y-auto">
                  <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono text-sm">
                    {atob(viewingFile.content.split(',')[1] || '')}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* No files message */}
      {userData.syllabusFiles.length === 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3">
            Why upload your syllabus?
          </h3>
          <ul className="space-y-2 text-gray-700 dark:text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-purple-600 dark:text-purple-400 mt-1">•</span>
              <span>Get a personalized learning roadmap based on your curriculum</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-600 dark:text-purple-400 mt-1">•</span>
              <span>Receive technology recommendations that complement your coursework</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-600 dark:text-purple-400 mt-1">•</span>
              <span>Compare your syllabus with real job requirements</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-600 dark:text-purple-400 mt-1">•</span>
              <span>Find internships relevant to your field of study</span>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
