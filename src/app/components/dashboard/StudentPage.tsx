import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Map, Lightbulb, Video, Briefcase, Plus, ArrowLeft, FileText, Eye, X, File as FileIcon, Trash2, Image, ChevronDown, Building2, ExternalLink, CheckCircle2, AlertCircle, Target, Loader2, Github, GraduationCap, Search, Play, BookOpen, Star, MapPin, Clock, DollarSign, CheckCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import SkillChip from '../ui/SkillChip';
import {
  apiErrorMessage,
  analyzeSkillGap,
  analyzeGitHubProfile,
  createStudentSkillTwin,
  extractSkills,
  getCareerAlignment,
  getCompletedSkillEvents,
  getLearningResources,
  getYouTubeLearningVideos,
  getLearningRoadmap,
  getProgress,
  getProgressSummary,
  getSkillProgress,
  getProjectRecommendations,
  initializeProgress,
  listCareerRoles,
  makeSelfDeclaredEvidence,
  updateSkillProgress,
  type CompletionEvent,
  type LearningResourceRecommendation,
  type YouTubeLearningVideo,
  type LearningRoadmapResponse,
  type ProgressRecord,
  type ProgressSummary,
  type ProjectRecommendation,
  type StudentEvidenceInput,
  type CareerAlignmentResponse,
  type SkillGapResponse,
} from '../../api';
import { useUser } from '../../context/UserContext';
import { toast } from 'sonner';

export default function StudentPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { userData, updateStudentSkills, removeStudentSkill, updateStudentSyllabus, removeSyllabusFile, updateStudentDetails } = useUser();
  const visibleSkills = [...new Set([...userData.profile.skills, ...userData.studentSkills])];
  const [newSkill, setNewSkill] = useState('');
  const [newSyllabusItem, setNewSyllabusItem] = useState('');
  const [isViewingResume, setIsViewingResume] = useState(false);
  const [viewingSyllabusFile, setViewingSyllabusFile] = useState<{fileName: string, content: string} | null>(null);
  
  // Academic fields state - initialize from userData or empty
  const [marks10th, setMarks10th] = useState(userData.marks10th || '');
  const [marks12th, setMarks12th] = useState(userData.marks12th || '');
  const [cgpa, setCgpa] = useState(userData.cgpa || '');
  const [githubProfile, setGithubProfile] = useState(userData.githubLink || '');
  const [savingAcademic, setSavingAcademic] = useState(false);

  // Sync state with userData when it changes
  useEffect(() => {
    setMarks10th(userData.marks10th || '');
    setMarks12th(userData.marks12th || '');
    setCgpa(userData.cgpa || '');
    setGithubProfile(userData.githubLink || '');
  }, [userData.marks10th, userData.marks12th, userData.cgpa, userData.githubLink]);

  const saveAcademicDetails = () => {
    setSavingAcademic(true);
    updateStudentDetails({
      marks10th,
      marks12th,
      cgpa,
      githubLink: githubProfile,
    });
    setTimeout(() => {
      setSavingAcademic(false);
      toast.success('Academic details saved!');
    }, 500);
  };

  const addSkill = () => {
    if (newSkill.trim()) {
      const updatedSkills = [...userData.studentSkills, newSkill.trim()];
      updateStudentSkills(updatedSkills);
      setNewSkill('');
      toast.success('Skill added!');
    }
  };

  const handleRemoveSkill = (skill: string) => {
    removeStudentSkill(skill);
    toast.success('Skill removed!');
  };

  const addSyllabusItem = () => {
    if (newSyllabusItem.trim()) {
      const updatedSyllabus = [...userData.studentSyllabus, newSyllabusItem.trim()];
      updateStudentSyllabus(updatedSyllabus);
      setNewSyllabusItem('');
      toast.success('Syllabus item added!');
    }
  };

  const removeSyllabusItem = (index: number) => {
    const updated = userData.studentSyllabus.filter((_, i) => i !== index);
    updateStudentSyllabus(updated);
    toast.success('Topic removed!');
  };

  // Helper to render file viewer modal
  const renderFileViewer = (
    file: { fileName: string; content: string },
    isOpen: boolean,
    onClose: () => void,
    title: string,
    color: string
  ) => {
    if (!isOpen) return null;
    return (
      <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <FileText className={`w-5 h-5 text-${color}-600 dark:text-${color}-400`} />
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">{file.fileName}</h3>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            </button>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {file.content.startsWith('data:application/pdf') ? (
              <iframe
                src={file.content}
                className="w-full h-[70vh] rounded-lg border border-gray-200 dark:border-gray-700"
                title={title}
              />
            ) : file.content.startsWith('data:image/') ? (
              <img src={file.content} alt={title} className="max-w-full mx-auto rounded-lg" />
            ) : (
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 max-h-[70vh] overflow-y-auto">
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono text-sm">
                  {atob(file.content.split(',')[1] || '')}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Show overview if on main student page
  if (location.pathname === '/dashboard/student') {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Student Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-300">
            Manage your learning journey and career preparation
          </p>
        </div>

        {/* Skills Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <h2 className="text-xl font-bold text-white mb-4 bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-2 rounded-lg inline-flex items-center gap-2 shadow-md">
            <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
            Your Skills
          </h2>
          <div className="mb-4">
            {visibleSkills.length > 0 ? (
              <div className="flex flex-wrap gap-2 mb-4">
                {visibleSkills.map((skill) => (
                  <SkillChip key={skill} tone="purple">
                    {skill}
                    <button
                      onClick={() => handleRemoveSkill(skill)}
                      className="ml-1 rounded-full p-0.5 opacity-60 transition-opacity hover:bg-purple-200 hover:opacity-100 dark:hover:bg-purple-800"
                      title="Remove skill"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </SkillChip>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 mb-4">No skills added yet</p>
            )}
            <div className="flex flex-col sm:flex-row gap-2">
              <Input
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                placeholder="Add a skill (e.g., Python, React, Data Analysis)"
                className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                onKeyPress={(e) => e.key === 'Enter' && addSkill()}
              />
              <Button onClick={addSkill} className="bg-purple-600 hover:bg-purple-700 sm:shrink-0">
                <Plus className="w-4 h-4 mr-2" />
                Add
              </Button>
            </div>
          </div>
        </div>

        {/* Academic & GitHub Info Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <h2 className="text-xl font-bold text-white mb-4 bg-gradient-to-r from-indigo-600 to-blue-600 px-4 py-2 rounded-lg inline-flex items-center gap-2 shadow-md">
            <GraduationCap className="w-5 h-5" />
            Academic & GitHub Info
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                10th Marks (%)
              </label>
              <Input
                type="text"
                value={marks10th}
                onChange={(e) => setMarks10th(e.target.value)}
                placeholder="e.g., 85"
                className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                12th Marks (%)
              </label>
              <Input
                type="text"
                value={marks12th}
                onChange={(e) => setMarks12th(e.target.value)}
                placeholder="e.g., 90"
                className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                CGPA
              </label>
              <Input
                type="text"
                value={cgpa}
                onChange={(e) => setCgpa(e.target.value)}
                placeholder="e.g., 8.5"
                className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">
                <Github className="w-4 h-4" /> GitHub Profile
              </label>
              <Input
                type="text"
                value={githubProfile}
                onChange={(e) => setGithubProfile(e.target.value)}
                placeholder="username or URL"
                className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
              />
            </div>
          </div>
          <Button 
            onClick={saveAcademicDetails} 
            disabled={savingAcademic}
            className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
          >
            {savingAcademic ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>Save Academic Details</>
            )}
          </Button>
          {(marks10th || marks12th || cgpa || githubProfile) && (
            <div className="mt-4 flex flex-wrap gap-2">
              {marks10th && (
                <span className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 rounded-full text-sm">
                  10th: {marks10th}%
                </span>
              )}
              {marks12th && (
                <span className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 rounded-full text-sm">
                  12th: {marks12th}%
                </span>
              )}
              {cgpa && (
                <span className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 rounded-full text-sm">
                  CGPA: {cgpa}
                </span>
              )}
              {githubProfile && (
                <a
                  href={githubProfile.startsWith('http') ? githubProfile : `https://github.com/${githubProfile}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm flex items-center gap-1 hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  <Github className="w-3 h-3" />
                  {githubProfile.includes('github.com') ? githubProfile.split('/').pop() : githubProfile}
                </a>
              )}
            </div>
          )}
        </div>

        {/* Syllabus Topics Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <h2 className="text-xl font-bold text-white mb-4 bg-gradient-to-r from-blue-600 to-cyan-600 px-4 py-2 rounded-lg inline-flex items-center gap-2 shadow-md">
            <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
            Syllabus Topics
          </h2>
          <div className="mb-4">
            {userData.studentSyllabus.length > 0 ? (
              <div className="space-y-2 mb-4">
                {userData.studentSyllabus.map((topic, index) => (
                  <div
                    key={index}
                    className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg flex items-center justify-between"
                  >
                    <p className="text-gray-900 dark:text-white">{topic}</p>
                    <button
                      onClick={() => removeSyllabusItem(index)}
                      className="p-1 hover:bg-blue-200 dark:hover:bg-blue-800 rounded transition-colors"
                      title="Remove topic"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                {userData.syllabusFiles.length > 0 
                  ? 'Add syllabus topics manually or they will be extracted from your files'
                  : 'Upload syllabus files or add topics manually'}
              </p>
            )}
            <div className="flex flex-col gap-2 sm:flex-row">
              <Input
                value={newSyllabusItem}
                onChange={(e) => setNewSyllabusItem(e.target.value)}
                placeholder="Add a syllabus topic (e.g., Machine Learning, Database Systems)"
                className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                onKeyPress={(e) => e.key === 'Enter' && addSyllabusItem()}
              />
              <Button onClick={addSyllabusItem} className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                <Plus className="w-4 h-4 mr-2" />
                Add
              </Button>
            </div>
          </div>
        </div>

        {/* Uploaded Syllabus Files Section */}
        {userData.syllabusFiles.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
            <h2 className="text-xl font-bold text-white mb-4 bg-gradient-to-r from-rose-500 to-pink-600 px-4 py-2 rounded-lg inline-flex items-center gap-2 shadow-md">
              <FileText className="w-5 h-5" />
              Uploaded Syllabus Files ({userData.syllabusFiles.length})
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {userData.syllabusFiles.map((file) => (
                <div
                  key={file.id}
                  className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 border border-gray-200 dark:border-gray-600 flex items-center gap-3"
                >
                  {file.type === 'pdf' ? (
                    <FileText className="w-8 h-8 text-red-500 flex-shrink-0" />
                  ) : file.type === 'image' ? (
                    <Image className="w-8 h-8 text-blue-500 flex-shrink-0" />
                  ) : (
                    <FileIcon className="w-8 h-8 text-gray-500 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white text-sm truncate">{file.fileName}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase">{file.type}</p>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => setViewingSyllabusFile({ fileName: file.fileName, content: file.content })}
                      className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                      title="View"
                    >
                      <Eye className="w-4 h-4 text-purple-500" />
                    </button>
                    <button
                      onClick={() => { removeSyllabusFile(file.id); toast.success('File removed'); }}
                      className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Syllabus File Viewer Modal */}
        {viewingSyllabusFile && renderFileViewer(
          viewingSyllabusFile,
          true,
          () => setViewingSyllabusFile(null),
          'Syllabus Preview',
          'purple'
        )}

        {/* Uploaded Resume Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <h2 className="text-xl font-bold text-white mb-4 bg-gradient-to-r from-emerald-500 to-green-600 px-4 py-2 rounded-lg inline-flex items-center gap-2 shadow-md">
            <FileIcon className="w-5 h-5" />
            Your Resume
          </h2>
          {userData.resume ? (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <FileIcon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <p className="text-gray-700 dark:text-gray-300 font-medium">{userData.resume.fileName}</p>
              </div>
              <Button
                onClick={() => setIsViewingResume(true)}
                className="bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
              >
                <Eye className="w-4 h-4 mr-2" />
                View Resume
              </Button>
              {renderFileViewer(userData.resume, isViewingResume, () => setIsViewingResume(false), 'Resume Preview', 'blue')}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              No resume uploaded yet. Go to the Resume section to upload one.
            </p>
          )}
        </div>

        {/* Action Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <button
            onClick={() => navigate('/dashboard/student/roadmap')}
            className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-2 border-transparent hover:border-orange-400 dark:hover:border-orange-500 text-left group"
          >
            <div className="p-3 bg-gradient-to-br from-orange-400 to-amber-500 rounded-lg w-fit mb-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg">
              <Map className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">Roadmap</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Get your personalized learning path
            </p>
          </button>

          <button
            onClick={() => navigate('/dashboard/student/recommendations')}
            className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-2 border-transparent hover:border-yellow-400 dark:hover:border-yellow-500 text-left group"
          >
            <div className="p-3 bg-gradient-to-br from-yellow-400 to-amber-500 rounded-lg w-fit mb-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg">
              <Lightbulb className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-yellow-600 dark:group-hover:text-yellow-400 transition-colors">Recommendations</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Technology and skill suggestions
            </p>
          </button>

          <button
            onClick={() => navigate('/dashboard/student/videos')}
            className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-2 border-transparent hover:border-red-400 dark:hover:border-red-500 text-left group"
          >
            <div className="p-3 bg-gradient-to-br from-red-500 to-rose-600 rounded-lg w-fit mb-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg">
              <Video className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors">Learning Videos</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Curated educational content
            </p>
          </button>

          <button
            onClick={() => navigate('/dashboard/student/internships')}
            className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-2 border-transparent hover:border-teal-400 dark:hover:border-teal-500 text-left group"
          >
            <div className="p-3 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-lg w-fit mb-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg">
              <Briefcase className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">Internships</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Find relevant opportunities
            </p>
          </button>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/roadmap" element={<RoadmapPage />} />
      <Route path="/recommendations" element={<RecommendationsPage />} />
      <Route path="/videos" element={<VideosPage />} />
      <Route path="/internships" element={<InternshipsPage />} />
    </Routes>
  );
}

// Sub-pages
type StudentEvidenceProfile = {
  profile: { skills: string[] };
  studentSkills: string[];
  resume: { skillEvidence?: StudentEvidenceInput[] } | null;
  githubLink: string;
  studentSyllabus: string[];
};

async function collectStudentEvidence(userData: StudentEvidenceProfile) {
  const records: StudentEvidenceInput[] = makeSelfDeclaredEvidence([
    ...userData.profile.skills,
    ...userData.studentSkills,
  ]);
  records.push(...(userData.resume?.skillEvidence ?? []));
  let githubProjects: Array<{ name: string; description: string; skills: string[]; url: string; stars: number }> = [];
  let githubUsername = userData.githubLink || '';
  if (githubUsername.includes('github.com/')) {
    githubUsername = githubUsername.split('github.com/').pop()?.split('/')[0] || '';
  }
  if (githubUsername) {
    const github = await analyzeGitHubProfile(githubUsername);
    githubProjects = github.projects;
    records.push(...github.skills.map((skill) => ({
      skill,
      source: 'github' as const,
      evidence: `Skill listed by GitHub profile analysis: ${skill}`,
      confidence: 'low' as const,
    })));
  }

  const syllabusText = userData.studentSyllabus.join('\n');
  if (syllabusText.trim()) {
    const syllabusSkills = await extractSkills(syllabusText);
    records.push(...syllabusSkills.extracted_skills.map((skill) => ({
      skill,
      source: 'syllabus' as const,
      evidence: `Skill mention in supplied syllabus topics: ${skill}`,
      confidence: 'low' as const,
    })));
  }

  // Resume parsing is performed in the Resume section; reuse its saved evidence here.
  const twin = await createStudentSkillTwin(records);
  const evidenceRecords: StudentEvidenceInput[] = twin.flatMap((record) => record.evidence.map((item) => ({
    skill: record.skill,
    source: item.source,
    evidence: item.evidence,
    proficiency: item.proficiency as StudentEvidenceInput['proficiency'],
    confidence: item.confidence as StudentEvidenceInput['confidence'],
  })));
  return { evidenceRecords, githubProjects };
}

function RoadmapPage() {
  const navigate = useNavigate();
  const { userData } = useUser();
  const declaredSkills = [...new Set([...userData.profile.skills, ...userData.studentSkills])];
  const studentId = userData.profile.email.trim().toLowerCase();
  const savedRoleKey = studentId ? `careeralign:lastRoadmapRole:${studentId}` : null;
  const [loading, setLoading] = useState(false);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [jobRoles, setJobRoles] = useState<string[]>([]);
  const [selectedJob, setSelectedJob] = useState<string | null>(() => {
    if (!savedRoleKey) return null;
    try { return localStorage.getItem(savedRoleKey); } catch { return null; }
  });
  const initiallySavedRole = useRef(selectedJob);
  const autoRestoreStarted = useRef(false);
  const [analysisData, setAnalysisData] = useState<{
    targetRole: string;
    roadmapId: string;
    gaps: SkillGapResponse;
    alignment: CareerAlignmentResponse;
    githubProjects: Array<{ name: string; description: string; skills: string[]; url: string; stars: number }>;
    roadmap: LearningRoadmapResponse;
    resources: LearningResourceRecommendation[];
    projects: ProjectRecommendation[];
    progress: ProgressRecord[];
    progressSummary: ProgressSummary;
    completionEvents: CompletionEvent[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progressError, setProgressError] = useState<string | null>(null);
  const [updatingSkill, setUpdatingSkill] = useState<string | null>(null);
  const [step, setStep] = useState<'select' | 'analyze'>('select');

  // Fetch the approved CareerAlign roles on mount.
  useEffect(() => {
    fetchJobRoles();
  }, []);

  const fetchJobRoles = async () => {
    setLoadingJobs(true);
    setError(null);
    try {
      setJobRoles(await listCareerRoles());
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoadingJobs(false);
    }
  };

  const analyzeAndGenerateRoadmap = async () => {
    if (!selectedJob) return;
    if (!studentId) {
      setError('Your profile email is needed to save and retrieve roadmap progress. Sign in with your profile first.');
      return;
    }
    if (savedRoleKey) {
      try { localStorage.setItem(savedRoleKey, selectedJob); } catch { /* MongoDB remains the progress store. */ }
    }
    
    setLoading(true);
    setError(null);
    try {
      const { evidenceRecords, githubProjects } = await collectStudentEvidence(userData);
      const gaps = await analyzeSkillGap(evidenceRecords, selectedJob);
      const alignment = await getCareerAlignment(evidenceRecords, selectedJob);
      const roadmap = await getLearningRoadmap(evidenceRecords, selectedJob);
      const resources = await getLearningResources(evidenceRecords, selectedJob);
      const projects = await getProjectRecommendations(evidenceRecords, selectedJob);
      const initialProgress = await initializeProgress(roadmap, studentId);
      setAnalysisData({
        targetRole: selectedJob,
        roadmapId: initialProgress.roadmap_id,
        gaps,
        alignment,
        githubProjects,
        roadmap,
        resources: resources.recommendations,
        projects: projects.recommendations,
        progress: initialProgress.progress,
        progressSummary: initialProgress.summary,
        completionEvents: [],
      });
      setProgressError(null);
      setStep('analyze');
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (
      initiallySavedRole.current &&
      initiallySavedRole.current === selectedJob &&
      jobRoles.includes(selectedJob) &&
      !autoRestoreStarted.current
    ) {
      autoRestoreStarted.current = true;
      void analyzeAndGenerateRoadmap();
    }
  }, [jobRoles, selectedJob]);

  const updateRoadmapProgress = async (skill: string, status: 'in_progress' | 'completed') => {
    setUpdatingSkill(skill);
    setProgressError(null);
    try {
      if (!studentId || !analysisData) throw new Error('Student profile or roadmap identity is unavailable.');
      await updateSkillProgress(skill, status, studentId, analysisData.roadmapId);
      const [skillProgress, progressState, progressSummary, completionState] = await Promise.all([
        getSkillProgress(skill, studentId, analysisData.roadmapId),
        getProgress(studentId, analysisData.roadmapId),
        getProgressSummary(studentId, analysisData.roadmapId),
        getCompletedSkillEvents(studentId, analysisData.roadmapId),
      ]);
      setAnalysisData((current) => current ? {
        ...current,
        progress: progressState.progress.map((item) => item.skill === skill ? skillProgress : item),
        progressSummary,
        completionEvents: completionState.newly_completed_skills,
      } : current);
    } catch (err) {
      setProgressError(apiErrorMessage(err));
    } finally {
      setUpdatingSkill(null);
    }
  };

  const roadmapStatusGroups = analysisData ? [
    {
      status: 'in_progress',
      title: 'In progress',
      steps: analysisData.roadmap.steps.filter((step) => (analysisData.progress.find((item) => item.skill === step.skill)?.status ?? step.status) === 'in_progress'),
    },
    {
      status: 'upcoming',
      title: 'Upcoming',
      steps: analysisData.roadmap.steps.filter((step) => {
        const status = analysisData.progress.find((item) => item.skill === step.skill)?.status ?? step.status;
        return status !== 'completed' && status !== 'in_progress';
      }),
    },
    {
      status: 'completed',
      title: 'Completed',
      steps: analysisData.roadmap.steps.filter((step) => (analysisData.progress.find((item) => item.skill === step.skill)?.status ?? step.status) === 'completed'),
    },
  ] : [];

  return (
    <div className="max-w-5xl mx-auto">
      <Button
        onClick={() => navigate('/dashboard/student')}
        variant="ghost"
        className="mb-6 hover:bg-gray-100 dark:hover:bg-gray-700"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Student Dashboard
      </Button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">🎯 Career Roadmap Generator</h1>
        <p className="text-gray-600 dark:text-gray-300">
              Select a target role to compare your declared skills and entered syllabus topics with observed role requirements.
        </p>
      </div>

      {/* Step 1: Select Job Role */}
      {step === 'select' && (
        <>
          {/* Info Banner */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-4 mb-6 border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Analysis will include:</p>
            <div className="flex flex-wrap gap-2">
              {userData.syllabusFiles.length > 0 && (
                <span className="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full text-sm flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  {userData.syllabusFiles.length} Syllabus file(s)
                </span>
              )}
              {declaredSkills.length > 0 && (
                <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full text-sm">
                  ✓ {declaredSkills.length} skills
                </span>
              )}
              {userData.studentSyllabus.length > 0 && (
                <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm">
                  ✓ {userData.studentSyllabus.length} topics
                </span>
              )}
              {userData.resume && (
                <span className="px-3 py-1 bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300 rounded-full text-sm flex items-center gap-1">
                  <FileText className="w-4 h-4" />
                  Resume
                </span>
              )}
              {userData.githubLink && (
                <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm flex items-center gap-1">
                  <Github className="w-4 h-4" />
                  GitHub
                </span>
              )}
              {userData.cgpa && (
                <span className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 rounded-full text-sm flex items-center gap-1">
                  <GraduationCap className="w-4 h-4" />
                  CGPA: {userData.cgpa}
                </span>
              )}
            </div>
          </div>

          {/* Loading target roles */}
          {loadingJobs && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-12 border border-gray-200 dark:border-gray-700 text-center">
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Loading CareerAlign roles...</h2>
            </div>
          )}

          {/* Job Roles Grid */}
          {!loadingJobs && jobRoles.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-blue-500" />
                Select a Target Career Role ({jobRoles.length} available)
              </h2>
              
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {jobRoles.map((role) => (
                  <button
                    key={role}
                    type="button"
                    onClick={() => setSelectedJob(role)}
                    className={`w-full min-w-0 rounded-xl border p-4 text-left transition-colors ${
                      selectedJob === role
                        ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-200 dark:bg-blue-950/40 dark:ring-blue-900'
                        : 'border-gray-200 bg-white hover:border-blue-300 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-700'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center text-white font-bold">
                        <Briefcase className="w-5 h-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <h3 className="break-words text-base font-semibold text-gray-900 dark:text-white">{role}</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">CareerAlign role</p>
                          </div>
                          {selectedJob === role && (
                            <CheckCircle2 className="w-6 h-6 text-blue-500 flex-shrink-0" />
                          )}
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Compare your available skill evidence against observed role skills.</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Analyze Button */}
              {selectedJob && (
                <div className="sticky bottom-3 z-20 rounded-xl border border-gray-200 bg-white/95 p-3 shadow-md backdrop-blur dark:border-gray-700 dark:bg-gray-800/95 sm:bottom-4 sm:p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">Selected: {selectedJob}</p>
                    </div>
                    <Button
                      onClick={analyzeAndGenerateRoadmap}
                      disabled={loading}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-6"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Target className="w-4 h-4 mr-2" />
                          Generate Roadmap
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 border border-red-200 dark:border-red-800 text-center">
              <p className="text-red-600 dark:text-red-400">{error}</p>
              <Button onClick={fetchJobRoles} className="mt-4 bg-red-600 hover:bg-red-700">
                Retry
              </Button>
            </div>
          )}
        </>
      )}

      {/* Step 2: Show Analysis and Roadmap */}
      {step === 'analyze' && analysisData && (
        <div className="space-y-6">
          {/* Back Button */}
          <Button
            onClick={() => { setStep('select'); setAnalysisData(null); }}
            variant="outline"
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Job Selection
          </Button>

          {/* Job Info Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
            <h2 className="text-2xl font-bold mb-2">Roadmap for: {analysisData.targetRole}</h2>
            <p className="text-blue-100">Career Readiness Score is skill alignment, not a hiring probability.</p>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="bg-white/15 rounded-lg px-4 py-3">
                <p className="text-3xl font-bold">{analysisData.alignment.career_readiness.career_readiness_score ?? '—'}{analysisData.alignment.career_readiness.career_readiness_score === null ? '' : '%'}</p>
                <p className="text-sm text-blue-100">Career Readiness</p>
              </div>
              <div className="bg-white/15 rounded-lg px-4 py-3">
                <p className="text-3xl font-bold">{analysisData.alignment.matched_count}</p>
                <p className="text-sm text-blue-100">Matched</p>
              </div>
              <div className="bg-white/15 rounded-lg px-4 py-3">
                <p className="text-3xl font-bold">{analysisData.alignment.partial_count + analysisData.alignment.missing_count}</p>
                <p className="text-sm text-blue-100">Partial + Missing</p>
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-xl p-4 border border-orange-200 dark:border-orange-800">
            <p className="text-gray-700 dark:text-gray-300">
              Backend skill-gap analysis found {analysisData.gaps.matched_count} matched, {analysisData.gaps.partial_count} partial, and {analysisData.gaps.missing_count} missing role skills.
            </p>
          </div>

          {/* GitHub Projects (if available) */}
          {analysisData.githubProjects.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-5 border border-gray-200 dark:border-gray-700">
              <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Github className="w-5 h-5" />
                Your GitHub Projects (Skills Extracted)
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                {analysisData.githubProjects.slice(0, 4).map((project) => (
                  <a
                    key={project.url || project.name}
                    href={project.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border hover:border-blue-300 dark:hover:border-blue-600 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900 dark:text-white text-sm">{project.name}</span>
                      <span className="text-xs text-gray-500">⭐ {project.stars}</span>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-1">{project.description}</p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {project.skills.slice(0, 3).map((skill) => (
                        <span key={skill} className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-xs">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Skills Comparison */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <section className="min-w-0 rounded-xl border border-green-200 bg-white p-5 dark:border-green-900 dark:bg-gray-800">
              <h3 className="mb-3 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
                <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" /> Matched ({analysisData.gaps.matched_count})
              </h3>
              <div className="flex flex-wrap gap-2">
                {analysisData.gaps.matched_skills.map((item) => <SkillChip key={item.skill} tone="green">{item.skill}</SkillChip>)}
                {analysisData.gaps.matched_count === 0 && <p className="text-sm text-gray-500 dark:text-gray-400">No matching skills yet.</p>}
              </div>
            </section>
            <section className="min-w-0 rounded-xl border border-amber-200 bg-white p-5 dark:border-amber-900 dark:bg-gray-800">
              <h3 className="mb-3 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
                <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400" /> Partial ({analysisData.gaps.partial_count})
              </h3>
              <div className="flex flex-wrap gap-2">
                {analysisData.gaps.partial_skills.map((item) => <SkillChip key={item.skill} tone="amber">{item.skill}</SkillChip>)}
                {analysisData.gaps.partial_count === 0 && <p className="text-sm text-gray-500 dark:text-gray-400">No partial skills identified.</p>}
              </div>
            </section>
            <section className="min-w-0 rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
              <h3 className="mb-3 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
                <Target className="h-5 w-5 text-blue-600 dark:text-blue-400" /> Missing ({analysisData.gaps.missing_count})
              </h3>
              <div className="flex flex-wrap gap-2">
                {analysisData.gaps.missing_skills.map((item) => <SkillChip key={item.skill} tone="slate">{item.skill}</SkillChip>)}
                {analysisData.gaps.missing_count === 0 && <p className="text-sm text-gray-500 dark:text-gray-400">No missing skills identified.</p>}
              </div>
            </section>
          </div>

          <section className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800 sm:p-6" aria-labelledby="roadmap-heading">
            <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 id="roadmap-heading" className="flex items-center gap-2 text-xl font-bold text-gray-900 dark:text-white">
                  <Map className="h-5 w-5 text-blue-600 dark:text-blue-400" /> Personalized Learning Roadmap
                </h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{analysisData.targetRole} · {analysisData.roadmap.steps.length} learning steps</p>
              </div>
              <span className="inline-flex self-start rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-800 dark:bg-blue-950/50 dark:text-blue-200">
                {analysisData.progressSummary.completion_percentage}% complete
              </span>
            </div>

            <div className="mb-5 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/50">
              <div className="mb-2 flex items-center justify-between gap-3 text-sm">
                <span className="font-medium text-gray-800 dark:text-gray-200">Learning progress</span>
                <span className="text-gray-600 dark:text-gray-400">{analysisData.progressSummary.completed_count} of {analysisData.progressSummary.total_skills} completed</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700" role="progressbar" aria-label="Roadmap completion" aria-valuemin={0} aria-valuemax={100} aria-valuenow={analysisData.progressSummary.completion_percentage}>
                <div className="h-full rounded-full bg-blue-600 transition-all" style={{ width: `${analysisData.progressSummary.completion_percentage}%` }} />
              </div>
              {progressError && <p role="alert" className="mt-2 text-sm text-red-600 dark:text-red-400">{progressError}</p>}
              {analysisData.completionEvents.length > 0 && <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">Completion records mean only that you marked a learning step complete; they do not infer proficiency.</p>}
            </div>

            {analysisData.roadmap.steps.length === 0 ? (
              <p className="text-sm text-gray-600 dark:text-gray-300">No learning steps are needed for this role based on the current profile.</p>
            ) : (
              <div className="space-y-3">
                {roadmapStatusGroups.map((group) => {
                  const groupTone = group.status === 'completed'
                    ? 'text-green-800 dark:text-green-300'
                    : group.status === 'in_progress'
                      ? 'text-blue-800 dark:text-blue-300'
                      : 'text-gray-800 dark:text-gray-200';
                  return (
                    <details key={group.status} className="group rounded-lg border border-gray-200 dark:border-gray-700" defaultOpen={group.status !== 'completed' && group.steps.length > 0}>
                      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-lg px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-900/40 [&::-webkit-details-marker]:hidden">
                        <span className={`font-semibold ${groupTone}`}>{group.title}</span>
                        <span className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                          {group.steps.length} {group.steps.length === 1 ? 'skill' : 'skills'}
                          <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
                        </span>
                      </summary>
                      <div className="grid grid-cols-1 gap-3 border-t border-gray-200 p-3 dark:border-gray-700 md:grid-cols-2 xl:grid-cols-3">
                        {group.steps.map((step) => {
                          const status = analysisData.progress.find((item) => item.skill === step.skill)?.status ?? step.status;
                          const statusClass = status === 'completed'
                            ? 'bg-green-50 text-green-800 dark:bg-green-950/50 dark:text-green-200'
                            : status === 'in_progress'
                              ? 'bg-blue-50 text-blue-800 dark:bg-blue-950/50 dark:text-blue-200'
                              : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200';
                          return (
                            <article key={step.step} className="flex min-w-0 flex-col rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                              <div className="mb-2 flex items-start justify-between gap-2">
                                <div className="min-w-0">
                                  <p className="text-xs text-gray-500 dark:text-gray-400">Step {step.step} · {step.priority} priority · {step.gap_type}</p>
                                  <h4 className="mt-1 break-words font-semibold text-gray-900 dark:text-white">{step.skill}</h4>
                                </div>
                                <span className={`shrink-0 rounded-full px-2 py-1 text-xs font-medium capitalize ${statusClass}`}>{status.replace('_', ' ')}</span>
                              </div>
                              <details className="mb-3 text-sm text-gray-600 dark:text-gray-300">
                                <summary className="cursor-pointer text-blue-700 hover:underline dark:text-blue-300">Step details</summary>
                                <p className="mt-2">{step.reason}</p>
                                {step.prerequisites.length > 0 && <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">Prerequisites: {step.prerequisites.join(', ')}</p>}
                              </details>
                              {status !== 'completed' && (
                                <div className="mt-auto flex flex-wrap gap-2">
                                  {status !== 'in_progress' && <Button size="sm" variant="outline" disabled={updatingSkill === step.skill} onClick={() => updateRoadmapProgress(step.skill, 'in_progress')}>{updatingSkill === step.skill ? 'Updating…' : 'Mark in progress'}</Button>}
                                  <Button size="sm" disabled={updatingSkill === step.skill} onClick={() => updateRoadmapProgress(step.skill, 'completed')}>{updatingSkill === step.skill ? 'Updating…' : 'Mark completed'}</Button>
                                </div>
                              )}
                            </article>
                          );
                        })}
                      </div>
                    </details>
                  );
                })}
              </div>
            )}
          </section>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Learning Resources</h3>
            {analysisData.resources.length === 0 ? <p className="text-gray-500">No catalog resources are currently available for these roadmap skills.</p> : (
              <div className="grid md:grid-cols-2 gap-3">
                {analysisData.resources.map((resource) => <div key={resource.resource_id} className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                  <p className="text-xs text-blue-600 dark:text-blue-400">{resource.skill} · {resource.level}</p>
                  <h4 className="font-semibold text-gray-900 dark:text-white">{resource.title}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{resource.description}</p>
                  {resource.url && <a className="text-sm text-blue-600 hover:underline mt-2 inline-flex items-center gap-1" href={resource.url} target="_blank" rel="noreferrer">{resource.provider}<ExternalLink className="w-3 h-3" /></a>}
                </div>)}
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Practical Projects</h3>
            {analysisData.projects.length === 0 ? <p className="text-gray-500">No catalog projects match the current skill gaps.</p> : (
              <div className="grid md:grid-cols-2 gap-3">
                {analysisData.projects.map((project) => <div key={project.project_id} className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                  <div className="flex justify-between gap-2"><h4 className="font-semibold text-gray-900 dark:text-white">{project.title}</h4><span className="text-xs text-gray-500">{project.difficulty}</span></div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">{project.description}</p>
                  <div className="mt-3 space-y-2">
                    <div>
                      <p className="mb-1 text-xs font-medium text-gray-500 dark:text-gray-400">Missing skills addressed</p>
                      <div className="flex flex-wrap gap-1.5">
                        {project.addressed_missing_skills.length
                          ? project.addressed_missing_skills.map((skill) => <SkillChip key={skill} tone="slate">{skill}</SkillChip>)
                          : <span className="text-xs text-gray-500 dark:text-gray-400">None</span>}
                      </div>
                    </div>
                    {project.addressed_partial_skills.length > 0 && <div>
                      <p className="mb-1 text-xs font-medium text-gray-500 dark:text-gray-400">Partial skills addressed</p>
                      <div className="flex flex-wrap gap-1.5">{project.addressed_partial_skills.map((skill) => <SkillChip key={skill} tone="amber">{skill}</SkillChip>)}</div>
                    </div>}
                  </div>
                  <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">{project.reason}</p>
                </div>)}
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}

function RecommendationsPage() {
  const navigate = useNavigate();
  const { userData } = useUser();
  const studentId = userData.profile.email.trim().toLowerCase();
  const savedRoleKey = studentId ? `careeralign:lastRoadmapRole:${studentId}` : null;
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState('');
  const [resources, setResources] = useState<LearningResourceRecommendation[] | null>(null);
  const [projects, setProjects] = useState<ProjectRecommendation[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    listCareerRoles().then((availableRoles) => {
      if (!active) return;
      setRoles(availableRoles);
      let savedRole = '';
      if (savedRoleKey) {
        try { savedRole = localStorage.getItem(savedRoleKey) || ''; } catch { /* Role selection can be made manually. */ }
      }
      if (availableRoles.includes(savedRole)) setSelectedRole(savedRole);
    }).catch((err) => {
      if (active) setError(apiErrorMessage(err));
    });
    return () => { active = false; };
  }, [savedRoleKey]);

  const loadRecommendations = async () => {
    if (!selectedRole) {
      setError('Select a target role to load its recommendations.');
      return;
    }
    setLoading(true);
    setError(null);
    setResources(null);
    setProjects(null);
    try {
      const { evidenceRecords } = await collectStudentEvidence(userData);
      const [resourceResult, projectResult] = await Promise.all([
        getLearningResources(evidenceRecords, selectedRole),
        getProjectRecommendations(evidenceRecords, selectedRole),
      ]);
      setResources(resourceResult.recommendations);
      setProjects(projectResult.recommendations);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <Button onClick={() => navigate('/dashboard/student')} variant="ghost" className="mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Student Dashboard
      </Button>
      <section className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800 sm:p-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Learning Recommendations</h1>
        <p className="mb-5 mt-1 text-sm text-gray-600 dark:text-gray-300">Get learning resources and practical project ideas for a target role. Your selected target role is not changed by this request.</p>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="min-w-0 flex-1 text-sm font-medium text-gray-700 dark:text-gray-200">
            Target role
            <select value={selectedRole} onChange={(event) => { setSelectedRole(event.target.value); setResources(null); setProjects(null); }} className="mt-1 block h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white">
              <option value="">{roles.length ? 'Select a role' : 'Loading roles…'}</option>
              {roles.map((role) => <option key={role} value={role}>{role}</option>)}
            </select>
          </label>
          <Button onClick={loadRecommendations} disabled={loading || !selectedRole} className="sm:shrink-0">
            {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Loading recommendations…</> : 'Show recommendations'}
          </Button>
        </div>
        {error && <p role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">{error}</p>}
        {(resources || projects) && <div className="mt-7 space-y-7" aria-live="polite">
          <section>
            <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Learning resources for {selectedRole}</h2>
            {!resources?.length ? <p className="text-sm text-gray-600 dark:text-gray-300">No learning resources are available for the current role gaps.</p> : <div className="grid grid-cols-1 gap-3 md:grid-cols-2">{resources.map((resource) => <article key={resource.resource_id} className="min-w-0 rounded-lg border border-gray-200 p-4 dark:border-gray-700"><p className="text-xs font-medium text-blue-700 dark:text-blue-300">{resource.skill} · {resource.level}</p><h3 className="mt-1 break-words font-semibold text-gray-900 dark:text-white">{resource.title}</h3><p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{resource.description}</p><p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{resource.provider}</p>{resource.url && <a href={resource.url} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-blue-700 hover:underline dark:text-blue-300">Open resource <ExternalLink className="h-3.5 w-3.5" /></a>}</article>)}</div>}
          </section>
          <section>
            <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Project recommendations</h2>
            {!projects?.length ? <p className="text-sm text-gray-600 dark:text-gray-300">No project recommendations are available for the current role gaps.</p> : <div className="grid grid-cols-1 gap-3 md:grid-cols-2">{projects.map((project) => <article key={project.project_id} className="min-w-0 rounded-lg border border-gray-200 p-4 dark:border-gray-700"><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="break-words font-semibold text-gray-900 dark:text-white">{project.title}</h3><span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs capitalize text-gray-700 dark:bg-gray-700 dark:text-gray-200">{project.difficulty}</span></div><p className="mt-2 text-sm text-gray-600 dark:text-gray-300">{project.description}</p><p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{project.reason}</p></article>)}</div>}
          </section>
        </div>}
      </section>
    </div>
  );
}

function VideosPage() {
  const navigate = useNavigate();
  const { userData } = useUser();
  const studentId = userData.profile.email.trim().toLowerCase();
  const savedRoleKey = studentId ? `careeralign:lastRoadmapRole:${studentId}` : null;
  const [selectedRole] = useState(() => {
    if (!savedRoleKey) return '';
    try { return localStorage.getItem(savedRoleKey) || ''; } catch { return ''; }
  });
  const [videos, setVideos] = useState<YouTubeLearningVideo[] | null>(null);
  const [topics, setTopics] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLearningVideos = async () => {
    if (!selectedRole) {
      return;
    }
    setLoading(true);
    setError(null);
    setVideos(null);
    setTopics([]);
    try {
      const { evidenceRecords } = await collectStudentEvidence(userData);
      const result = await getYouTubeLearningVideos(evidenceRecords, selectedRole);
      setVideos(result.videos);
      setTopics(result.topics);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <Button onClick={() => navigate('/dashboard/student')} variant="ghost" className="mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Student Dashboard
      </Button>
      <section className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800 sm:p-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <Video className="w-6 h-6 text-red-500" /> Learning Videos
        </h1>
        <p className="mb-5 text-sm text-gray-600 dark:text-gray-300">
          Find role-relevant tutorials on YouTube. Curated CareerAlign documentation and courses remain available separately under Learning Recommendations.
        </p>
        {selectedRole ? <>
          <p className="mb-4 text-sm font-medium text-gray-800 dark:text-gray-200">Selected role: <span className="font-semibold">{selectedRole}</span></p>
          <Button onClick={loadLearningVideos} disabled={loading} className="sm:shrink-0">
            {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Searching YouTube…</> : 'Find learning videos'}
          </Button>
        </> : <p className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-200">Select a target career role to get personalized YouTube learning recommendations.</p>}
        {error && <p role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">{error}</p>}
        {videos && (
          <div className="mt-6" aria-live="polite">
            <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">YouTube tutorials for {selectedRole}</h2>
            {videos.length === 0 ? (
              <p className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300">No relevant learning videos were found for this role.</p>
            ) : (
              <>
                {topics.length > 0 && <p className="mb-3 text-xs text-gray-500 dark:text-gray-400">Search topics: {topics.join(' · ')}</p>}
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                {videos.map((video) => (
                  <article key={video.video_id} className="min-w-0 overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
                    {video.thumbnail_url && <a href={video.youtube_url} target="_blank" rel="noopener noreferrer" aria-label={`Watch ${video.title} on YouTube`}><img src={video.thumbnail_url} alt="" loading="lazy" className="aspect-video w-full object-cover" /></a>}
                    <div className="p-4">
                      <p className="mb-1 text-xs font-medium text-blue-700 dark:text-blue-300">{video.topic}</p>
                      <h3 className="line-clamp-2 min-h-10 break-words font-semibold text-gray-900 dark:text-white">{video.title}</h3>
                      {video.channel_title && <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{video.channel_title}</p>}
                      {video.description && <p className="mt-2 line-clamp-3 text-sm text-gray-600 dark:text-gray-300">{video.description}</p>}
                      <a className="mt-4 inline-flex items-center gap-1 rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700" href={video.youtube_url} target="_blank" rel="noopener noreferrer">Watch on YouTube <ExternalLink className="h-3.5 w-3.5" /></a>
                    </div>
                  </article>
                ))}
                </div>
              </>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

function InternshipsPage() {
  const navigate = useNavigate();
  const { userData } = useUser();
  const internshipProfileSkills = [...userData.profile.skills, ...userData.studentSkills];
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'recommended' | 'matched'>('all');

  const allInternships = [
    {
      company: 'Google',
      role: 'Software Engineering Intern',
      location: 'Mountain View, CA',
      duration: 'Summer 2026',
      stipend: '$8,000/month',
      skills: ['Python', 'Java', 'Data Structures', 'Algorithms'],
      color: 'blue',
      category: 'Software Development',
    },
    {
      company: 'Microsoft',
      role: 'Product Management Intern',
      location: 'Redmond, WA',
      duration: '3-6 months',
      stipend: '$7,500/month',
      skills: ['Product Strategy', 'Analytics', 'Communication', 'SQL'],
      color: 'green',
      category: 'Product Management',
    },
    {
      company: 'Amazon',
      role: 'Full Stack Developer Intern',
      location: 'Seattle, WA',
      duration: 'Summer 2026',
      stipend: '$7,800/month',
      skills: ['React', 'Node.js', 'AWS', 'JavaScript', 'TypeScript'],
      color: 'orange',
      category: 'Web Development',
    },
    {
      company: 'Meta',
      role: 'Data Science Intern',
      location: 'Menlo Park, CA',
      duration: '12 weeks',
      stipend: '$8,200/month',
      skills: ['Python', 'Machine Learning', 'Statistics', 'TensorFlow', 'Data Analysis'],
      color: 'purple',
      category: 'Data Science',
    },
    {
      company: 'Netflix',
      role: 'UI/UX Design Intern',
      location: 'Los Gatos, CA',
      duration: 'Summer 2026',
      stipend: '$7,000/month',
      skills: ['Figma', 'User Research', 'Prototyping', 'CSS', 'Design Systems'],
      color: 'red',
      category: 'Design',
    },
    {
      company: 'Salesforce',
      role: 'Cloud Engineering Intern',
      location: 'San Francisco, CA',
      duration: '3 months',
      stipend: '$7,200/month',
      skills: ['AWS', 'Docker', 'Kubernetes', 'Linux', 'CI/CD'],
      color: 'teal',
      category: 'Cloud/DevOps',
    },
    {
      company: 'Apple',
      role: 'iOS Developer Intern',
      location: 'Cupertino, CA',
      duration: 'Summer 2026',
      stipend: '$8,500/month',
      skills: ['Swift', 'iOS', 'Xcode', 'UIKit', 'SwiftUI'],
      color: 'gray',
      category: 'Mobile Development',
    },
    {
      company: 'Spotify',
      role: 'Backend Engineer Intern',
      location: 'Stockholm, Sweden',
      duration: '6 months',
      stipend: '$6,500/month',
      skills: ['Java', 'Python', 'Microservices', 'PostgreSQL', 'REST APIs'],
      color: 'green',
      category: 'Backend Development',
    },
    {
      company: 'Adobe',
      role: 'Machine Learning Intern',
      location: 'San Jose, CA',
      duration: 'Summer 2026',
      stipend: '$7,600/month',
      skills: ['Python', 'PyTorch', 'Deep Learning', 'Computer Vision', 'NLP'],
      color: 'red',
      category: 'Machine Learning',
    },
    {
      company: 'LinkedIn',
      role: 'Frontend Developer Intern',
      location: 'Sunnyvale, CA',
      duration: '3 months',
      stipend: '$7,400/month',
      skills: ['React', 'JavaScript', 'CSS', 'HTML', 'TypeScript'],
      color: 'blue',
      category: 'Web Development',
    },
    {
      company: 'Stripe',
      role: 'Security Engineer Intern',
      location: 'San Francisco, CA',
      duration: 'Summer 2026',
      stipend: '$8,000/month',
      skills: ['Python', 'Security', 'Networking', 'Cryptography', 'Linux'],
      color: 'purple',
      category: 'Security',
    },
    {
      company: 'Airbnb',
      role: 'Data Engineer Intern',
      location: 'San Francisco, CA',
      duration: '4 months',
      stipend: '$7,300/month',
      skills: ['Python', 'SQL', 'Apache Spark', 'ETL', 'Data Warehousing'],
      color: 'orange',
      category: 'Data Engineering',
    },
  ];

  // Calculate match percentage based on user skills
  const calculateMatchPercentage = (internshipSkills: string[]) => {
    if (!internshipProfileSkills || internshipProfileSkills.length === 0) return 0;
    const userSkillsLower = internshipProfileSkills.map(s => s.toLowerCase());
    const matchingSkills = internshipSkills.filter(skill => 
      userSkillsLower.some(userSkill => 
        skill.toLowerCase().includes(userSkill) || userSkill.includes(skill.toLowerCase())
      )
    );
    return Math.round((matchingSkills.length / internshipSkills.length) * 100);
  };

  // Get matching skills for highlighting
  const getMatchingSkills = (internshipSkills: string[]) => {
    if (!internshipProfileSkills || internshipProfileSkills.length === 0) return [];
    const userSkillsLower = internshipProfileSkills.map(s => s.toLowerCase());
    return internshipSkills.filter(skill => 
      userSkillsLower.some(userSkill => 
        skill.toLowerCase().includes(userSkill) || userSkill.includes(skill.toLowerCase())
      )
    );
  };

  // Filter internships based on search query and filter type
  const filteredInternships = useMemo(() => {
    let results = allInternships.map(internship => ({
      ...internship,
      matchPercentage: calculateMatchPercentage(internship.skills),
      matchingSkills: getMatchingSkills(internship.skills),
    }));

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      results = results.filter(internship =>
        internship.company.toLowerCase().includes(query) ||
        internship.role.toLowerCase().includes(query) ||
        internship.category.toLowerCase().includes(query) ||
        internship.skills.some(skill => skill.toLowerCase().includes(query))
      );
    }

    // Apply active filter
    if (activeFilter === 'recommended') {
      results = results.filter(i => i.matchPercentage > 0);
    } else if (activeFilter === 'matched') {
      results = results.filter(i => i.matchPercentage >= 50);
    }

    // Sort by match percentage (highest first)
    results.sort((a, b) => b.matchPercentage - a.matchPercentage);

    return results;
  }, [searchQuery, activeFilter, internshipProfileSkills]);

  const getMatchBadgeColor = (percentage: number) => {
    if (percentage >= 75) return 'bg-gradient-to-r from-green-500 to-emerald-500 text-white';
    if (percentage >= 50) return 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white';
    if (percentage >= 25) return 'bg-gradient-to-r from-yellow-500 to-amber-500 text-white';
    return 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
  };

  const getBorderColor = (color: string) => {
    const colors: Record<string, string> = {
      blue: 'hover:border-blue-500',
      green: 'hover:border-green-500',
      orange: 'hover:border-orange-500',
      purple: 'hover:border-purple-500',
      red: 'hover:border-red-500',
      teal: 'hover:border-teal-500',
      gray: 'hover:border-gray-500',
    };
    return colors[color] || 'hover:border-blue-500';
  };

  const getGradientBg = (color: string) => {
    const gradients: Record<string, string> = {
      blue: 'from-blue-500 to-blue-600',
      green: 'from-green-500 to-emerald-600',
      orange: 'from-orange-500 to-amber-600',
      purple: 'from-purple-500 to-violet-600',
      red: 'from-red-500 to-rose-600',
      teal: 'from-teal-500 to-cyan-600',
      gray: 'from-gray-500 to-slate-600',
    };
    return gradients[color] || 'from-blue-500 to-blue-600';
  };

  return (
    <div className="max-w-6xl mx-auto">
      <Button
        onClick={() => navigate('/dashboard/student')}
        variant="ghost"
        className="mb-6 hover:bg-gray-100 dark:hover:bg-gray-700 hover:scale-105 transition-all duration-300"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Student Dashboard
      </Button>

      {/* Header with Gradient */}
      <div className="mb-8 bg-gradient-to-r from-teal-600 via-cyan-600 to-blue-600 rounded-2xl p-8 text-white shadow-xl">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
            <Briefcase className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-bold">Internship Opportunities</h1>
        </div>
        <p className="text-white/90 text-lg">
          Find internships matching your skills and career goals
        </p>
        {internshipProfileSkills && internshipProfileSkills.length > 0 && (
          <div className="mt-4 flex items-center gap-2 text-sm">
            <Star className="w-4 h-4" />
            <span>Personalized recommendations based on your {internshipProfileSkills.length} skills</span>
          </div>
        )}
      </div>

      {/* Search and Filter Section */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8 border border-gray-200 dark:border-gray-700">
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              type="text"
              placeholder="Search by company, role, skill, or category (e.g., React, Data Science, Google)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 pr-4 py-3 w-full text-lg border-2 border-gray-200 dark:border-gray-600 focus:border-teal-500 dark:focus:border-teal-400 rounded-xl transition-colors duration-300"
            />
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setActiveFilter('all')}
            className={`px-5 py-2.5 rounded-xl font-medium transition-all duration-300 ${
              activeFilter === 'all'
                ? 'bg-gradient-to-r from-teal-500 to-cyan-600 text-white shadow-lg scale-105'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 hover:scale-105'
            }`}
          >
            All Internships ({allInternships.length})
          </button>
          <button
            onClick={() => setActiveFilter('recommended')}
            className={`px-5 py-2.5 rounded-xl font-medium transition-all duration-300 ${
              activeFilter === 'recommended'
                ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg scale-105'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 hover:scale-105'
            }`}
          >
            <Star className="w-4 h-4 inline mr-1" />
            Recommended
          </button>
          <button
            onClick={() => setActiveFilter('matched')}
            className={`px-5 py-2.5 rounded-xl font-medium transition-all duration-300 ${
              activeFilter === 'matched'
                ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg scale-105'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 hover:scale-105'
            }`}
          >
            <CheckCircle className="w-4 h-4 inline mr-1" />
            Best Match (50%+)
          </button>
        </div>

        {/* Show user skills */}
        {internshipProfileSkills && internshipProfileSkills.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Your Skills:</p>
            <div className="flex flex-wrap gap-2">
              {internshipProfileSkills.slice(0, 10).map((skill, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-gradient-to-r from-teal-100 to-cyan-100 dark:from-teal-900 dark:to-cyan-900 text-teal-700 dark:text-teal-300 rounded-full text-sm font-medium"
                >
                  {skill}
                </span>
              ))}
              {internshipProfileSkills.length > 10 && (
                <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full text-sm">
                  +{internshipProfileSkills.length - 10} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Results Count */}
      <div className="mb-6 text-gray-600 dark:text-gray-400">
        Showing {filteredInternships.length} internship{filteredInternships.length !== 1 ? 's' : ''}
        {searchQuery && ` for "${searchQuery}"`}
      </div>

      {/* Internships Grid */}
      {filteredInternships.length > 0 ? (
        <div className="grid md:grid-cols-2 gap-6">
          {filteredInternships.map((internship, index) => (
            <div
              key={index}
              className={`bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border-2 border-transparent ${getBorderColor(internship.color)} hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 group relative overflow-hidden`}
            >
              {/* Match Percentage Badge */}
              {internshipProfileSkills && internshipProfileSkills.length > 0 && (
                <div className={`absolute top-4 right-4 px-3 py-1.5 rounded-full text-sm font-bold ${getMatchBadgeColor(internship.matchPercentage)} shadow-md`}>
                  {internship.matchPercentage}% Match
                </div>
              )}

              {/* Company Header */}
              <div className="flex items-start gap-4 mb-4">
                <div className={`p-3 bg-gradient-to-br ${getGradientBg(internship.color)} rounded-xl shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-300`}>
                  <Briefcase className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1 pr-16">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
                    {internship.company}
                  </h3>
                  <p className="text-lg text-gray-700 dark:text-gray-300">{internship.role}</p>
                  <span className="inline-block mt-1 px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                    {internship.category}
                  </span>
                </div>
              </div>

              {/* Details */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                  <MapPin className="w-4 h-4 text-gray-400" />
                  <span className="text-sm">{internship.location}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span className="text-sm">{internship.duration}</span>
                </div>
                <div className="flex items-center gap-2 text-green-600 dark:text-green-400 font-semibold">
                  <DollarSign className="w-4 h-4" />
                  <span className="text-sm">{internship.stipend}</span>
                </div>
              </div>

              {/* Skills */}
              <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Required Skills:</p>
                <div className="flex flex-wrap gap-2">
                  {internship.skills.map((skill, skillIndex) => {
                    const isMatched = internship.matchingSkills.includes(skill);
                    return (
                      <span
                        key={skillIndex}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-all duration-300 ${
                          isMatched
                            ? 'bg-gradient-to-r from-green-100 to-emerald-100 dark:from-green-900 dark:to-emerald-900 text-green-700 dark:text-green-300 ring-2 ring-green-400 dark:ring-green-600'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {isMatched && <CheckCircle className="w-3 h-3 inline mr-1" />}
                        {skill}
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* Apply Button */}
              <Button className={`w-full mt-4 bg-gradient-to-r ${getGradientBg(internship.color)} hover:opacity-90 text-white shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300`}>
                <ExternalLink className="w-4 h-4 mr-2" />
                Apply Now
              </Button>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-12 text-center border border-gray-200 dark:border-gray-700">
          <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-full w-fit mx-auto mb-4">
            <Search className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No internships found</h3>
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            Try adjusting your search or filters to find more opportunities
          </p>
          <Button
            onClick={() => {
              setSearchQuery('');
              setActiveFilter('all');
            }}
            className="bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300"
          >
            Clear Filters
          </Button>
        </div>
      )}
    </div>
  );
}
