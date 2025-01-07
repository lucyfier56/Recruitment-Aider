'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'

// Mock analysis data (replace this with actual data fetching logic)
const mockAnalysis = `
Analysis for Rupin Ajay Software Engineer Resume.pdf
Job Description: JD.txt
------------------------------
### Candidate Analysis
#### 1. Candidate Summary
* Brief professional snapshot: Student with a strong academic background and hands-on project experience, eager to apply problem-solving skills and passion for innovation.
* Years of experience: 3 months of internship experience as a Data Engineer Intern.
* Standout achievements: Top 10 finishes in Google Hack4Change and OpenHack 2024, development of impactful projects such as Business Intelligence Automation and Dermatology Diagnosis and Reporting Tool.

... (truncated for brevity)

#### 12. Alternative Role Designation
* The job description could also be used for a Junior Software Engineer or a Python Developer role, with a focus on developing skills and experience in Python and FastAPI.
`

export default function AnalysisModal({ open, onOpenChange, application }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Analysis for {application?.name}</DialogTitle>
        </DialogHeader>
        <ScrollArea className="flex-grow">
          <div className="space-y-4 p-4">
            <pre className="whitespace-pre-wrap font-mono text-sm">
              {mockAnalysis}
            </pre>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}

