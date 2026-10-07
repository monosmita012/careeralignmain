import { useEffect, useState } from 'react';
import { Upload, FileText, CheckCircle, Eye, X, File as FileIcon, Loader2, Target } from 'lucide-react';
import { Button } from '../ui/button';
import SkillChip from '../ui/SkillChip';
import { useUser } from '../../context/UserContext';
import { toast } from 'sonner';
import {
  apiErrorMessage,
  enhanceResume,
  listCareerRoles,
  processResume,
  type ResumeEnhancementResponse,
} from '../../api';

export default function ResumePage() {
  const { userData, uploadResume } = useUser();
  const [isDragging, setIsDragging] = useState(false);
  const [isViewing, setIsViewing] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [enhancing, setEnhancing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enhancementError, setEnhancementError] = useState<string | null>(null);
  const [targetRole, setTargetRole] = useState('');
  const [availableRoles, setAvailableRoles] = useState<string[]>([]);
  const [enhancement, setEnhancement] = useState<ResumeEnhancementResponse | null>(null);

  useEffect(() => {
    listCareerRoles().then(setAvailableRoles).catch((roleError: unknown) => {
      setEnhancementError(apiErrorMessage(roleError));
    });
  }, []);

  const readFileAsDataUrl = (file: File) => new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => typeof reader.result === 'string' ? resolve(reader.result) : reject(new Error('Could not read the uploaded file.'));
    reader.onerror = () => reject(new Error('Could not read the uploaded file.'));
    reader.readAsDataURL(file);
  });

  const handleFileUpload = async (file: File) => {
    setProcessing(true);
    setError(null);
    try {
      const processed = await processResume(file);
      const content = await readFileAsDataUrl(file);
      uploadResume(file.name, content, processed.extracted_skills, processed.skill_evidence);
      setEnhancement(null);
      setEnhancementError(null);
      toast.success(`Resume processed. ${processed.extracted_skills.length} canonical skills found.`);
    } catch (uploadError) {
      const message = apiErrorMessage(uploadError);
      setError(message);
      toast.error(message);
    } finally {
      setProcessing(false);
    }
  };

  const runEnhancement = async () => {
    if (!userData.resume?.extractedSkills) {
      setEnhancementError('Process a resume before requesting enhancement feedback.');
      return;
    }
    setEnhancing(true);
    setEnhancementError(null);
    try {
      const blob = await fetch(userData.resume.content).then((response) => response.blob());
      const file = new File([blob], userData.resume.fileName, { type: blob.type });
      setEnhancement(await enhanceResume(file, targetRole || undefined));
    } catch (requestError) {
      setEnhancementError(apiErrorMessage(requestError));
    } finally {
      setEnhancing(false);
    }
  };

  const processSavedResume = async () => {
    if (!userData.resume) return;
    try {
      const blob = await fetch(userData.resume.content).then((response) => response.blob());
      await handleFileUpload(new File([blob], userData.resume.fileName, { type: blob.type }));
    } catch (resumeError) {
      const message = apiErrorMessage(resumeError);
      setError(message);
      toast.error(message);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Upload Resume</h1>
        <p className="text-gray-600 dark:text-gray-300">
          Upload your resume to get personalized job recommendations and career insights
        </p>
      </div>

      {userData.resume ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
              <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Resume Uploaded</h2>
              <div className="flex items-center gap-2 mt-1">
                <FileIcon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <p className="text-gray-600 dark:text-gray-300 font-medium">{userData.resume.fileName}</p>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                {userData.resume.extractedSkills
                  ? `${userData.resume.extractedSkills.length} canonical skills are ready for Skill Analysis and roadmap generation.`
                  : 'This saved resume has not been processed yet. Process it to add resume evidence to your Skill Twin.'}
              </p>
            </div>
          </div>

          {userData.resume.extractedSkills && userData.resume.extractedSkills.length > 0 ? (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">Skills detected in this resume</h3>
              <div className="flex flex-wrap gap-2">
                {userData.resume.extractedSkills.map((skill) => <SkillChip key={skill}>{skill}</SkillChip>)}
              </div>
            </div>
          ) : userData.resume.extractedSkills ? (
            <p className="mb-6 text-sm text-gray-600 dark:text-gray-300">No skills from the current CareerAlign taxonomy were detected in this resume.</p>
          ) : null}

          {/* View Resume Modal */}
          {isViewing && (
            <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
                <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">{userData.resume.fileName}</h3>
                  </div>
                  <button
                    onClick={() => setIsViewing(false)}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                  </button>
                </div>
                <div className="flex-1 overflow-auto p-4">
                  {userData.resume.content.startsWith('data:application/pdf') ? (
                    <iframe
                      src={userData.resume.content}
                      className="w-full h-[70vh] rounded-lg border border-gray-200 dark:border-gray-700"
                      title="Resume Preview"
                    />
                  ) : userData.resume.content.startsWith('data:image/') ? (
                    <img
                      src={userData.resume.content}
                      alt="Resume"
                      className="max-w-full mx-auto rounded-lg"
                    />
                  ) : (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 max-h-[70vh] overflow-y-auto">
                      <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono text-sm">
                        {atob(userData.resume.content.split(',')[1] || '')}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:gap-3">
            {!userData.resume.extractedSkills && (
              <Button onClick={processSavedResume} disabled={processing} className="bg-blue-600 hover:bg-blue-700 text-white">
                {processing ? 'Processing resume...' : 'Process Saved Resume'}
              </Button>
            )}
            <Button
              onClick={() => setIsViewing(true)}
              className="bg-green-600 hover:bg-green-700 text-white shadow-md hover:shadow-lg transition-all"
            >
              <Eye className="w-4 h-4 mr-2" />
              View Resume
            </Button>
            <Button
              onClick={() => document.getElementById('resume-upload')?.click()}
              disabled={processing}
              className="bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transition-all"
            >
              <Upload className="w-4 h-4 mr-2" />
              Upload New Resume
            </Button>
          </div>
          <input
            id="resume-upload"
            type="file"
            accept=".txt,.pdf,.docx"
            onChange={handleFileInput}
            className="hidden"
          />
          {error && <p role="alert" className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p>}
        </div>
      ) : (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-10 border-2 border-dashed transition-colors ${
            isDragging
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
          }`}
        >
          <div className="text-center">
            <div className="p-4 bg-blue-100 dark:bg-blue-900 rounded-full w-fit mx-auto mb-6">
              <FileText className="w-12 h-12 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">Upload Your Resume</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Drag and drop your file here, or click to browse
            </p>
            <Button
              onClick={() => document.getElementById('resume-upload')?.click()}
              disabled={processing}
              className="bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transition-all"
            >
              <Upload className="w-4 h-4 mr-2" />
              {processing ? 'Processing resume...' : 'Choose File'}
            </Button>
            <input
              id="resume-upload"
              type="file"
              accept=".txt,.pdf,.docx"
              onChange={handleFileInput}
              className="hidden"
            />
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
              Supported formats: TXT, PDF, DOCX (up to 10 MB)
            </p>
            {error && <p role="alert" className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p>}
          </div>
        </div>
      )}

      <section className="mt-8 bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3 mb-2">
          <Target className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Resume Enhancement</h2>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-5">
          Review resume sections, detectable writing patterns, and optional target-role skill coverage. This is an explainable content check, not an ATS score.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 items-end">
          <label className="flex-1 text-sm font-medium text-gray-700 dark:text-gray-200">
            Target career role (optional)
            <select
              value={targetRole}
              onChange={(event) => { setTargetRole(event.target.value); setEnhancement(null); }}
              className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white"
            >
              <option value="">General feedback only</option>
              {availableRoles.map((role) => <option key={role} value={role}>{role}</option>)}
            </select>
          </label>
          <Button onClick={runEnhancement} disabled={enhancing || !userData.resume?.extractedSkills} className="bg-purple-600 hover:bg-purple-700 text-white">
            {enhancing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Target className="w-4 h-4 mr-2" />}
            {enhancing ? 'Reviewing resume...' : 'Analyze Resume'}
          </Button>
        </div>
        {!userData.resume && <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">Upload and process a resume to receive feedback.</p>}
        {userData.resume && !userData.resume.extractedSkills && <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">Process the saved resume above before requesting enhancement feedback.</p>}
        {enhancementError && <p role="alert" className="mt-4 text-sm text-red-600 dark:text-red-400">{enhancementError}</p>}

        {enhancement && (
          <div className="mt-6 space-y-5" aria-live="polite">
            <p className="rounded-lg bg-purple-50 dark:bg-purple-900/20 p-4 text-gray-800 dark:text-gray-100">{enhancement.summary}</p>

            <div className="grid md:grid-cols-2 gap-4">
              <section className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Resume strengths</h3>
                {enhancement.strengths.length ? <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700 dark:text-gray-300">{enhancement.strengths.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="text-sm text-gray-500">No strengths detected by these checks.</p>}
              </section>
              <section className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Sections to review</h3>
                {enhancement.section_completeness.missing_sections.length ? (
                  <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700 dark:text-gray-300">
                    {enhancement.section_completeness.missing_sections.map((section) => <li key={section}>{section.replaceAll('_', ' ')}</li>)}
                  </ul>
                ) : <p className="text-sm text-gray-700 dark:text-gray-300">All checked sections appear in the resume.</p>}
                <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{enhancement.section_completeness.applicability_note}</p>
              </section>
            </div>

            <section className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Skill coverage</h3>
              <div className="space-y-3">
                <div>
                  <p className="mb-2 text-sm text-gray-600 dark:text-gray-300">Skills represented in the resume</p>
                  {enhancement.skill_coverage.resume_skills.length
                    ? <div className="flex flex-wrap gap-2">{enhancement.skill_coverage.resume_skills.map((skill) => <SkillChip key={skill}>{skill}</SkillChip>)}</div>
                    : <p className="text-sm text-gray-500 dark:text-gray-400">No canonical skills detected.</p>}
                </div>
                {enhancement.skill_coverage.skills_needing_stronger_evidence.length > 0 && <div>
                  <p className="mb-2 text-sm text-amber-700 dark:text-amber-300">Consider adding genuine project, experience, or certification evidence for:</p>
                  <div className="flex flex-wrap gap-2">{enhancement.skill_coverage.skills_needing_stronger_evidence.map((skill) => <SkillChip key={skill} tone="amber">{skill}</SkillChip>)}</div>
                </div>}
              </div>
              {enhancement.target_role_coverage && (
                <div className="mt-4 border-t border-gray-200 dark:border-gray-700 pt-4">
                  <h4 className="font-medium text-gray-900 dark:text-white">{enhancement.target_role_coverage.target_role} role coverage</h4>
                  <div className="mt-3 space-y-3">
                    <div>
                      <p className="mb-2 text-sm text-gray-600 dark:text-gray-300">Role skills represented</p>
                      {enhancement.target_role_coverage.represented_skills.length
                        ? <div className="flex flex-wrap gap-2">{enhancement.target_role_coverage.represented_skills.map((item) => <SkillChip key={item.skill} tone="green">{item.skill}</SkillChip>)}</div>
                        : <p className="text-sm text-gray-500 dark:text-gray-400">None detected.</p>}
                    </div>
                    <div>
                      <p className="mb-2 text-sm text-gray-600 dark:text-gray-300">Important role skills not represented in this resume</p>
                      {enhancement.target_role_coverage.not_represented_skills.length
                        ? <div className="flex flex-wrap gap-2">{enhancement.target_role_coverage.not_represented_skills.slice(0, 12).map((item) => <SkillChip key={item.skill} tone="slate">{item.skill}</SkillChip>)}</div>
                        : <p className="text-sm text-gray-500 dark:text-gray-400">None detected.</p>}
                    </div>
                  </div>
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{enhancement.target_role_coverage.note}</p>
                </div>
              )}
            </section>

            <section className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Content suggestions</h3>
              <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                {enhancement.suggestions.map((item, index) => <li key={`${item.topic}-${index}`}><span className="font-medium capitalize">{item.priority}:</span> {item.suggestion}</li>)}
              </ul>
              <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                Heuristic checks: {enhancement.content_checks.vague_phrase_count} vague phrase(s), {enhancement.content_checks.repeated_sentence_count} repeated sentence(s), and {enhancement.content_checks.measurable_line_count} line(s) with detectable measurements.
              </p>
            </section>
          </div>
        )}
      </section>

      {/* Information Section */}
      <div className="mt-8 bg-gradient-to-r from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-xl p-6 border border-green-200 dark:border-green-800 transition-colors duration-300">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3">
          Why upload your resume?
        </h3>
        <ul className="space-y-2 text-gray-700 dark:text-gray-300">
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-1">•</span>
            <span>Get matched with job roles that fit your experience and skills</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-1">•</span>
            <span>Discover companies actively hiring for your skill set</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-1">•</span>
            <span>Receive personalized recommendations for career advancement</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-1">•</span>
            <span>Identify skill gaps and get suggestions for improvement</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
